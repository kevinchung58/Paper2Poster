from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
import os
from pathlib import Path
import shutil

from ..database import crud, models_db
from ..database.database_setup import SessionLocal
from ..schemas import models as schemas
from .. import config
from ..services import poster_service

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from ..utils.pptx_generator import generate_pptx_from_data
from ..utils.preview_generator import background_convert_and_update_status

from fastapi.responses import FileResponse, JSONResponse
import logging
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/posters", response_model=schemas.APICreatePosterResponse, status_code=status.HTTP_201_CREATED)
async def create_poster_session(request: schemas.OriginalCreatePosterRequest, db: Session = Depends(get_db)):
    poster_create_data = schemas.PosterCreate(
        title=f"New Poster: {request.topic}" if request.topic else "New Untitled Poster",
        abstract=f"Abstract for poster on {request.topic}." if request.topic else "Initial abstract.",
        sections=[],
        selected_theme="default",
    )
    try:
        db_poster = crud.create_poster(db=db, poster_data=poster_create_data)
    except Exception as e:
        logger.error(f"Error creating poster in DB: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create poster in database.")

    pydantic_poster = schemas.Poster.from_orm(db_poster)
    return schemas.APICreatePosterResponse(
        poster_id=pydantic_poster.poster_id,
        poster_data=pydantic_poster,
        preview_image_url=f"/api/v1/posters/{pydantic_poster.poster_id}/preview"
    )

@router.get("/posters/{poster_id}", response_model=schemas.Poster)
async def get_poster_data_endpoint(poster_id: str, db: Session = Depends(get_db)):
    db_poster = crud.get_poster(db=db, poster_id=poster_id)
    if not db_poster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poster not found")
    return schemas.Poster.from_orm(db_poster)

@router.post("/posters/{poster_id}/prompt", response_model=schemas.APILLMPromptResponse)
async def handle_llm_prompt(
    poster_id: str,
    request: schemas.OriginalLLMPromptRequest,
    db: Session = Depends(get_db)
):
    try:
        updated_db_poster, response_message = poster_service.process_poster_update(
            db=db,
            poster_id=poster_id,
            request=request
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Critical error during poster update for {poster_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error calling poster_service for {poster_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the request.")

    final_pydantic_poster = schemas.Poster.from_orm(updated_db_poster)
    return schemas.APILLMPromptResponse(
        poster_id=final_pydantic_poster.poster_id,
        llm_response_text=response_message,
        updated_poster_data=final_pydantic_poster,
        preview_image_url=f"/api/v1/posters/{final_pydantic_poster.poster_id}/preview"
    )

@router.get("/posters/{poster_id}/preview")
async def get_poster_preview(
    poster_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_poster = crud.get_poster(db=db, poster_id=poster_id)
    if not db_poster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poster not found")

    pptx_to_convert_path_str: Optional[str] = None
    if not db_poster.pptx_file_path or not Path(db_poster.pptx_file_path).exists() or \
       (db_poster.pptx_file_path and Path(db_poster.pptx_file_path).exists() and db_poster.last_modified.replace(tzinfo=None) > datetime.fromtimestamp(Path(db_poster.pptx_file_path).stat().st_mtime)):
        logger.info(f"PPTX for poster {poster_id} needs generation/update for preview.")
        canonical_pptx_path = config.TEMP_POSTERS_DIR / f"{poster_id}.pptx"
        try:
            pydantic_poster = schemas.Poster.from_orm(db_poster)
            generate_pptx_from_data(pydantic_poster, str(canonical_pptx_path))
            db_poster = crud.update_poster_filepaths(db=db, poster_id=poster_id, pptx_path=str(canonical_pptx_path), preview_path=db_poster.preview_image_path)
            if not db_poster: raise HTTPException(status_code=500, detail="Failed to update PPTX path after regeneration.")
            pptx_to_convert_path_str = str(canonical_pptx_path)
        except Exception as e:
            logger.error(f"Error regenerating PPTX for preview {poster_id}: {e}", exc_info=True)
            update_data = schemas.PosterUpdate(preview_status="failed", preview_last_error=f"Failed to generate PPTX for preview: {str(e)}")
            crud.update_poster_data(db, poster_id=poster_id, poster_update=update_data)
            raise HTTPException(status_code=500, detail=f"Failed to generate PPTX for preview: {str(e)}")
    else:
        pptx_to_convert_path_str = str(db_poster.pptx_file_path)

    needs_preview_regeneration = False
    if db_poster.preview_status == "failed":
        needs_preview_regeneration = True
    elif not db_poster.preview_image_path or not Path(db_poster.preview_image_path).exists():
        needs_preview_regeneration = True
    elif db_poster.preview_image_path and Path(db_poster.preview_image_path).exists() and pptx_to_convert_path_str:
        preview_file = Path(db_poster.preview_image_path)
        pptx_file = Path(pptx_to_convert_path_str)
        try:
            if pptx_file.stat().st_mtime > preview_file.stat().st_mtime:
                needs_preview_regeneration = True
        except FileNotFoundError:
            needs_preview_regeneration = True

    if needs_preview_regeneration and db_poster.preview_status != "generating":
        logger.info(f"Regenerating preview for poster {poster_id}. Current status: {db_poster.preview_status}")
        db_poster = crud.update_poster_data(db, poster_id=poster_id, poster_update=schemas.PosterUpdate(preview_status="pending"))
        if not db_poster: raise HTTPException(status_code=500, detail="Failed to update poster status.")
        background_tasks.add_task(background_convert_and_update_status, poster_id, pptx_to_convert_path_str, str(config.TEMP_PREVIEWS_DIR.resolve()))
        return JSONResponse(status_code=202, content=schemas.Poster.from_orm(db_poster).dict())

    if db_poster.preview_status in ["generating", "pending"]:
        return JSONResponse(status_code=202, content=schemas.Poster.from_orm(db_poster).dict())

    if db_poster.preview_status == "completed" and db_poster.preview_image_path and Path(db_poster.preview_image_path).exists():
        return FileResponse(db_poster.preview_image_path, media_type="image/png", filename=f"preview_{poster_id}.png")

    if db_poster.preview_status == "failed":
        return JSONResponse(status_code=500, content={"detail": "Preview generation failed previously.", "poster_id": poster_id, "preview_status": "failed", "preview_last_error": db_poster.preview_last_error})

    logger.warning(f"Inconsistent preview state for poster {poster_id}: status {db_poster.preview_status}, path {db_poster.preview_image_path}")
    raise HTTPException(status_code=500, detail="Preview state is inconsistent. Please try again.")

@router.post("/posters/{poster_id}/generate_pptx", response_model=schemas.APIGeneratePPTXResponse)
async def trigger_pptx_generation(poster_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_poster = crud.get_poster(db=db, poster_id=poster_id)
    if not db_poster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poster not found")

    pydantic_poster = schemas.Poster.from_orm(db_poster)
    output_filename = f"{poster_id}.pptx"
    output_path = config.TEMP_POSTERS_DIR / output_filename

    try:
        generate_pptx_from_data(pydantic_poster, str(output_path))
    except Exception as e:
        logger.error(f"Error in trigger_pptx_generation (file gen) for {poster_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate PPTX file: {str(e)}")

    updated_db_poster = crud.update_poster_filepaths(db=db, poster_id=poster_id, pptx_path=str(output_path), preview_path=db_poster.preview_image_path)
    if not updated_db_poster:
         raise HTTPException(status_code=500, detail="Failed to update PPTX file path in database.")

    db_poster = crud.update_poster_data(db, poster_id=poster_id, poster_update=schemas.PosterUpdate(preview_status="pending"))
    if not db_poster:
        raise HTTPException(status_code=500, detail="Failed to set poster status to pending for preview generation.")

    background_tasks.add_task(background_convert_and_update_status, poster_id, str(output_path), str(config.TEMP_PREVIEWS_DIR.resolve()))

    return schemas.APIGeneratePPTXResponse(
        poster_id=poster_id,
        download_url=f"/api/v1/posters/{poster_id}/download_pptx",
        message="PPTX generation successful. Preview update initiated in background."
    )

@router.get("/posters/{poster_id}/download_pptx", response_class=FileResponse)
async def download_pptx_file(poster_id: str, db: Session = Depends(get_db)):
    db_poster = crud.get_poster(db=db, poster_id=poster_id)
    if not db_poster or not db_poster.pptx_file_path or not os.path.exists(str(db_poster.pptx_file_path)):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PPTX file not generated or found for this poster.")

    file_path_str = str(db_poster.pptx_file_path)
    return FileResponse(
        path=file_path_str,
        filename=f"poster_{poster_id}.pptx",
        media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation'
    )

@router.post(
    "/posters/{poster_id}/sections/{section_id}/upload_image",
    response_model=schemas.Poster,
    summary="Upload an image for a specific poster section"
)
async def upload_image_for_section_endpoint(
    poster_id: str,
    section_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    image_file: UploadFile = File(...)
):
    logger.info(f"Image upload request for poster '{poster_id}', section '{section_id}'. Filename: {image_file.filename}")

    db_poster = crud.get_poster(db, poster_id=poster_id)
    if not db_poster:
        logger.warning(f"Upload failed: Poster '{poster_id}' not found.")
        raise HTTPException(status_code=404, detail="Poster not found")

    target_section_orm = next((s for s in db_poster.sections if s.section_id == section_id), None)
    if not target_section_orm:
        logger.warning(f"Upload failed: Section '{section_id}' not found in poster '{poster_id}'.")
        raise HTTPException(status_code=404, detail=f"Section {section_id} not found in poster {poster_id}")

    file_extension = Path(image_file.filename if image_file.filename else "").suffix.lower()
    if not image_file.filename or file_extension not in config.ALLOWED_IMAGE_EXTENSIONS:
        logger.warning(f"Upload failed: Invalid file type for '{image_file.filename}'. Allowed: {config.ALLOWED_IMAGE_EXTENSIONS}")
        raise HTTPException(status_code=400, detail=f"Invalid image file type. Allowed extensions: {config.ALLOWED_IMAGE_EXTENSIONS}")

    contents = await image_file.read()
    if len(contents) > config.MAX_IMAGE_UPLOAD_SIZE_MB * 1024 * 1024:
        logger.warning(f"Upload failed: File '{image_file.filename}' exceeds size limit of {config.MAX_IMAGE_UPLOAD_SIZE_MB}MB.")
        raise HTTPException(status_code=413, detail=f"Image file size exceeds limit of {config.MAX_IMAGE_UPLOAD_SIZE_MB}MB.")
    await image_file.seek(0)

    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    section_upload_dir = config.UPLOADED_IMAGES_DIR / f"poster_{poster_id}" / f"section_{section_id}"
    os.makedirs(section_upload_dir, exist_ok=True)

    file_save_path = section_upload_dir / unique_filename
    relative_file_path_to_store = str(Path(config.UPLOADED_IMAGES_DIR_NAME) / f"poster_{poster_id}" / f"section_{section_id}" / unique_filename)

    try:
        with open(file_save_path, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
        logger.info(f"Image '{unique_filename}' saved to '{file_save_path}' for section '{section_id}'.")
    except Exception as e:
        logger.error(f"Failed to save uploaded image '{unique_filename}' to path '{file_save_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not save uploaded image.")
    finally:
        await image_file.close()

    current_image_urls = list(target_section_orm.image_urls or [])
    current_image_urls.append(relative_file_path_to_store)

    updated_sections_for_payload = []
    for s_orm in db_poster.sections:
        sec_dict = schemas.Section.from_orm(s_orm).dict()
        if s_orm.section_id == section_id:
            sec_dict['image_urls'] = current_image_urls
        updated_sections_for_payload.append(schemas.SectionCreate(**sec_dict))

    poster_update_payload = schemas.PosterUpdate(sections=updated_sections_for_payload)

    updated_db_poster = crud.update_poster_data(
        db=db, poster_id=poster_id, poster_update=poster_update_payload
    )
    if not updated_db_poster:
        logger.error(f"Failed to update poster data for poster '{poster_id}' after adding image path to section '{section_id}'.")
        try:
            os.remove(file_save_path)
            logger.info(f"Cleaned up orphaned image file: {file_save_path}")
        except OSError as e_remove:
            logger.error(f"Error cleaning up orphaned image file {file_save_path}: {e_remove}")
        raise HTTPException(status_code=500, detail="Failed to update poster data with new image path.")

    final_updated_db_poster = crud.update_poster_data(db, poster_id=poster_id, poster_update=schemas.PosterUpdate(preview_status="pending"))
    if not final_updated_db_poster:
        final_updated_db_poster = updated_db_poster
        logger.warning(f"Failed to update preview status for poster '{poster_id}' after image upload, but returning poster data.")

    logger.info(f"Image path '{relative_file_path_to_store}' added to section '{section_id}'. Poster '{poster_id}' updated. Preview status set to pending.")
    return schemas.Poster.from_orm(final_updated_db_poster)