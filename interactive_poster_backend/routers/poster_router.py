from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
import os
from pathlib import Path

# Database related imports
from ..database import crud, models_db
from ..database.database_setup import SessionLocal
from ..schemas import models as schemas
from .. import config

# CAMEL and utilities
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from ..utils.pptx_generator import generate_pptx_from_data
from ..utils.preview_generator import convert_pptx_to_png_soffice, background_convert_and_update_status

# FastAPI response types
from fastapi.responses import FileResponse, JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# --- Dependency for DB Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@router.post("/posters", response_model=schemas.APICreatePosterResponse, status_code=status.HTTP_201_CREATED)
async def create_poster_session(
    request: schemas.OriginalCreatePosterRequest,
    db: Session = Depends(get_db)
):
    poster_create_data = schemas.PosterCreate(
        title=f"New Poster: {request.topic}" if request.topic else "New Untitled Poster",
        abstract=f"Abstract for poster on {request.topic}." if request.topic else "Initial abstract.",
        sections=[],
        theme="default_theme",
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
    db_poster = crud.get_poster(db=db, poster_id=poster_id)
    if not db_poster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poster not found")

    current_pydantic_poster = schemas.Poster.from_orm(db_poster)
    update_payload_dict = {}
    llm_generated_content_for_update: Optional[str] = None
    actual_llm_text_output_for_chat: str = ""
    # Flag to indicate if the main content processing (LLM or targeted direct update) should be skipped
    skip_further_content_processing = False

    # 1. Handle theme update
    if request.selected_theme is not None and current_pydantic_poster.selected_theme != request.selected_theme:
        update_payload_dict["selected_theme"] = request.selected_theme
        current_pydantic_poster.selected_theme = request.selected_theme
        actual_llm_text_output_for_chat = f"Theme updated to '{request.selected_theme}'. "

    # 2. Handle style_overrides update
    if request.style_overrides is not None:
        update_payload_dict["style_overrides"] = request.style_overrides
        current_pydantic_poster.style_overrides = request.style_overrides
        if not actual_llm_text_output_for_chat:
            actual_llm_text_output_for_chat = "Style overrides applied. "
        else:
            actual_llm_text_output_for_chat += "Style overrides also applied. "

    # 3. Handle direct update of full sections array (e.g., for image URL changes)
    if request.is_direct_update and request.sections is not None:
        # This implies replacing all sections with the provided list.
        update_payload_dict["sections"] = request.sections
        sections_update_message = "Poster sections (e.g., image URLs) updated directly. "
        if actual_llm_text_output_for_chat:
            actual_llm_text_output_for_chat += sections_update_message
        else:
            actual_llm_text_output_for_chat = sections_update_message
        # If sections are fully replaced, typically no other prompt_text processing is needed for content in this call
        skip_further_content_processing = True

    # 4. Handle prompt text (LLM call or targeted direct update for non-section fields)
    if request.prompt_text is not None and not skip_further_content_processing:
        if request.is_direct_update: # Direct update for a specific non-section field
            if not request.target_element_id or request.target_element_id.startswith("section_"):
                actual_llm_text_output_for_chat += "Error: Direct content update via prompt_text requires a non-section target element (e.g., poster_title, poster_abstract). For section updates, use the 'sections' array with is_direct_update. "
            else:
                llm_generated_content_for_update = request.prompt_text
                actual_llm_text_output_for_chat += f"Content for '{request.target_element_id}' was directly updated. "
        else: # Process via LLM
            llm_contextual_prompt = ""
            # Build contextual prompt based on current_pydantic_poster (which includes theme/style changes)
            if request.target_element_id == "poster_title":
                llm_contextual_prompt = f"You are editing the title of a poster. Current title: '{current_pydantic_poster.title}'. Theme: '{current_pydantic_poster.selected_theme}'. User instruction: '{request.prompt_text}'. Respond with only the new title text."
            elif request.target_element_id == "poster_abstract":
                llm_contextual_prompt = f"You are editing the abstract of poster '{current_pydantic_poster.title}' (Theme: '{current_pydantic_poster.selected_theme}'). Current abstract: '{current_pydantic_poster.abstract}'. User instruction: '{request.prompt_text}'. Respond with only the new abstract text."
            elif request.target_element_id == "poster_conclusion":
                llm_contextual_prompt = f"Editing conclusion for poster '{current_pydantic_poster.title}' (Theme: '{current_pydantic_poster.selected_theme}'). Current: '{current_pydantic_poster.conclusion}'. Instruction: '{request.prompt_text}'. Respond with new text."
            elif request.target_element_id and request.target_element_id.startswith("section_"):
                parts = request.target_element_id.split('_')
                if len(parts) == 3:
                    sec_id, target_type = parts[1], parts[2]
                    target_section_obj = next((s for s in current_pydantic_poster.sections if s.section_id == sec_id), None)
                    if target_section_obj:
                        field_name = "title" if target_type == "title" else "content"
                        current_val = target_section_obj.section_title if target_type == "title" else target_section_obj.section_content
                        llm_contextual_prompt = f"Editing section {field_name} for section '{target_section_obj.section_title}' on poster '{current_pydantic_poster.title}'. Current {field_name}: '{current_val}'. User instruction: '{request.prompt_text}'. Respond with new text."
                    else: actual_llm_text_output_for_chat += f"Error: Section {sec_id} not found for LLM update. "
                else: actual_llm_text_output_for_chat += f"Error: Malformed section target {request.target_element_id}. "
            elif not request.target_element_id: # General prompt
                 llm_contextual_prompt = f"Poster: '{current_pydantic_poster.title}' (Theme: '{current_pydantic_poster.selected_theme}'). Abstract: '{current_pydantic_poster.abstract}'. User instruction: '{request.prompt_text}'. Provide general suggestions. If suggesting change to a specific field, make it clear."
            else: actual_llm_text_output_for_chat += f"Error: Unknown target '{request.target_element_id}' for LLM. "

            if llm_contextual_prompt and not ("Error:" in actual_llm_text_output_for_chat and "not found" in actual_llm_text_output_for_chat):
                try:
                    agent = ChatAgent(system_message=BaseMessage.make_assistant_message(role_name="Poster Content Assistant", content="Provide only the new text for the field being edited."))
                    llm_response_obj = agent.step(input_message=BaseMessage.make_user_message(role_name="User", content=llm_contextual_prompt))
                    if llm_response_obj.msgs and llm_response_obj.msgs[0].content:
                        llm_generated_content_for_update = llm_response_obj.msgs[0].content.strip()
                        actual_llm_text_output_for_chat += f"LLM response: \"{llm_generated_content_for_update}\". "
                    elif llm_response_obj.info and llm_response_obj.info.get('termination_reasons'):
                        actual_llm_text_output_for_chat += f"LLM call issue: {str(llm_response_obj.info['termination_reasons'])}. "
                    else: actual_llm_text_output_for_chat += "LLM produced no content update. "
                except Exception as e: actual_llm_text_output_for_chat += f"LLM service error: {str(e)}. "

        if llm_generated_content_for_update is not None and request.target_element_id:
            if request.target_element_id == "poster_title": update_payload_dict["title"] = llm_generated_content_for_update
            elif request.target_element_id == "poster_abstract": update_payload_dict["abstract"] = llm_generated_content_for_update
            elif request.target_element_id == "poster_conclusion": update_payload_dict["conclusion"] = llm_generated_content_for_update
            elif request.target_element_id.startswith("section_") and "sections" not in update_payload_dict: # Avoid overwriting full sections update
                parts = request.target_element_id.split('_')
                if len(parts) == 3:
                    sec_id, target_type = parts[1], parts[2]
                    temp_sections_data = [s.dict() for s in current_pydantic_poster.sections]
                    section_updated_in_list = False
                    for i, sec_dict_data in enumerate(temp_sections_data): # Use dict data for modification
                        if current_pydantic_poster.sections[i].section_id == sec_id:
                            if target_type == "title": temp_sections_data[i]["section_title"] = llm_generated_content_for_update
                            elif target_type == "content": temp_sections_data[i]["section_content"] = llm_generated_content_for_update
                            section_updated_in_list = True
                            break
                    if section_updated_in_list: update_payload_dict["sections"] = [schemas.SectionCreate(**s) for s in temp_sections_data]

    if not update_payload_dict and not request.prompt_text :
         if not actual_llm_text_output_for_chat: actual_llm_text_output_for_chat = "No update action performed (no changes specified)."
    elif not actual_llm_text_output_for_chat and update_payload_dict :
         actual_llm_text_output_for_chat = "Poster attributes updated."

    if update_payload_dict:
        poster_update_schema = schemas.PosterUpdate(**update_payload_dict)
        updated_db_poster = crud.update_poster_data(db=db, poster_id=poster_id, poster_update=poster_update_schema)
        if not updated_db_poster:
            raise HTTPException(status_code=500, detail="Failed to save poster updates to database.")
        db_poster = updated_db_poster

    final_pydantic_poster = schemas.Poster.from_orm(db_poster)
    return schemas.APILLMPromptResponse(
        poster_id=final_pydantic_poster.poster_id,
        llm_response_text=actual_llm_text_output_for_chat.strip(),
        updated_poster_data=final_pydantic_poster,
        preview_image_url=f"/api/v1/posters/{final_pydantic_poster.poster_id}/preview"
    )

@router.get("/posters/{poster_id}/preview")
async def get_poster_preview(
    poster_id: str,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = Depends()
):
    # ... (existing preview logic - should be mostly fine) ...
    db_poster = crud.get_poster(db=db, poster_id=poster_id)
    if not db_poster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Poster not found")

    pptx_to_convert_path_str: Optional[str] = None

    if not db_poster.pptx_file_path or not Path(db_poster.pptx_file_path).exists() or \
       (Path(db_poster.pptx_file_path).exists() and db_poster.last_modified.replace(tzinfo=None) > datetime.fromtimestamp(Path(db_poster.pptx_file_path).stat().st_mtime)):

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
            crud.update_poster_preview_status(db, poster_id=poster_id, status="failed", error_message=f"Failed to generate PPTX for preview: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate PPTX for preview: {str(e)}")
    else:
        pptx_to_convert_path_str = str(db_poster.pptx_file_path)

    needs_preview_regeneration = False
    if db_poster.preview_status == "failed":
        needs_preview_regeneration = True
    elif db_poster.preview_status != "completed" or not db_poster.preview_image_path or not Path(db_poster.preview_image_path).exists():
        needs_preview_regeneration = True
    elif db_poster.preview_image_path and Path(db_poster.preview_image_path).exists():
        preview_file = Path(db_poster.preview_image_path)
        pptx_file = Path(pptx_to_convert_path_str)
        try:
            if pptx_file.stat().st_mtime > preview_file.stat().st_mtime or \
               db_poster.last_modified.timestamp() > preview_file.stat().st_mtime:
                needs_preview_regeneration = True
        except FileNotFoundError:
             needs_preview_regeneration = True

    if needs_preview_regeneration and db_poster.preview_status != "generating":
        logger.info(f"Regenerating preview for poster {poster_id}. Current status: {db_poster.preview_status}")
        db_poster = crud.update_poster_preview_status(db, poster_id=poster_id, status="pending")
        if not db_poster: raise HTTPException(status_code=500, detail="Failed to update poster status.")

        background_tasks.add_task(
            background_convert_and_update_status,
            poster_id,
            pptx_to_convert_path_str,
            str(config.TEMP_PREVIEWS_DIR.resolve())
        )
        return JSONResponse(
            status_code=202,
            content=schemas.Poster.from_orm(db_poster).dict()
        )

    if db_poster.preview_status == "generating" or db_poster.preview_status == "pending":
        return JSONResponse(status_code=202, content=schemas.Poster.from_orm(db_poster).dict())

    if db_poster.preview_status == "completed" and db_poster.preview_image_path and Path(db_poster.preview_image_path).exists():
        return FileResponse(db_poster.preview_image_path, media_type="image/png", filename=f"preview_{poster_id}.png")

    if db_poster.preview_status == "failed":
        return JSONResponse(status_code=500, content={"detail": "Preview generation failed previously.", "poster_id": poster_id, "preview_status": "failed", "preview_last_error": db_poster.preview_last_error, "poster_data": schemas.Poster.from_orm(db_poster).dict()})

    logger.warning(f"Inconsistent preview state for poster {poster_id}: status {db_poster.preview_status}, path {db_poster.preview_image_path}")
    return JSONResponse(status_code=202, content={"message": "Preview not available or state is inconsistent. Try again shortly.", "poster_id": poster_id, "preview_status": db_poster.preview_status, "poster_data": schemas.Poster.from_orm(db_poster).dict()})

@router.post("/posters/{poster_id}/generate_pptx", response_model=schemas.APIGeneratePPTXResponse)
async def trigger_pptx_generation(poster_id: str, db: Session = Depends(get_db), background_tasks: BackgroundTasks = Depends()):
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
    db_poster = updated_db_poster

    crud.update_poster_preview_status(db, poster_id=poster_id, status="pending")
    background_tasks.add_task(
        background_convert_and_update_status,
        poster_id,
        str(output_path),
        str(config.TEMP_PREVIEWS_DIR.resolve())
    )

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
