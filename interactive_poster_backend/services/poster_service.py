# This service will contain the core business logic for poster manipulation.
from sqlalchemy.orm import Session
from ..schemas import models as schemas
from ..database import crud, models_db
from ..enums import PosterElement
from camel.agents import ChatAgent
from camel.messages import BaseMessage
from typing import Optional, Tuple
import shutil
import os
from pathlib import Path
import logging
from .. import config

logger = logging.getLogger(__name__)

def _delete_uploaded_image_file(relative_path: str):
    """Deletes a single uploaded image file, ensuring path safety."""
    if not relative_path or relative_path.startswith(('http://', 'https://')):
        return

    if ".." in Path(relative_path).parts:
        logger.warning(f"Skipping deletion for potentially unsafe path: {relative_path}")
        return

    full_path = config.UPLOADED_IMAGES_DIR / relative_path
    try:
        resolved_path = full_path.resolve()
        if config.UPLOADED_IMAGES_DIR.resolve() not in resolved_path.parents:
            logger.warning(f"Skipping deletion for path outside designated upload dir: {resolved_path}")
            return

        if resolved_path.is_file():
            resolved_path.unlink()
            logger.info(f"Deleted uploaded image file: {resolved_path}")
    except Exception as e:
        logger.error(f"Error deleting uploaded image file {full_path}: {e}", exc_info=True)

def process_poster_update(
    db: Session,
    poster_id: str,
    request: schemas.OriginalLLMPromptRequest
) -> Tuple[models_db.DbPoster, str]:
    """
    Handles the complex logic of updating a poster based on a prompt request.
    This includes direct updates, style changes, and LLM-based content generation.
    """
    db_poster = crud.get_poster(db=db, poster_id=poster_id)
    if not db_poster:
        raise ValueError("Poster not found")

    current_pydantic_poster = schemas.Poster.from_orm(db_poster)
    update_payload_dict = {}
    llm_generated_content_for_update: Optional[str] = None
    response_message: str = ""
    skip_llm_or_direct_field_prompt_processing = False

    # 1. Handle Theme and Style Updates
    if request.selected_theme is not None and current_pydantic_poster.selected_theme != request.selected_theme:
        update_payload_dict["selected_theme"] = request.selected_theme
        current_pydantic_poster.selected_theme = request.selected_theme
        response_message = f"Theme updated to '{request.selected_theme}'. "

    if request.style_overrides is not None:
        update_payload_dict["style_overrides"] = request.style_overrides
        current_pydantic_poster.style_overrides = request.style_overrides
        response_message += "Style overrides applied. "

    # 2. Handle Direct Section Updates
    if request.is_direct_update and request.sections is not None:
        update_payload_dict["sections"] = request.sections
        response_message += "Poster sections updated directly. "
        skip_llm_or_direct_field_prompt_processing = True

    # 3. Handle LLM or Direct Content Updates via Prompt Text
    if request.prompt_text is not None and not skip_llm_or_direct_field_prompt_processing:
        if request.is_direct_update:
            if not request.target_element_id or PosterElement.is_section_element(request.target_element_id):
                response_message += "Error: Direct content update requires a non-section target (e.g., poster_title). "
            else:
                llm_generated_content_for_update = request.prompt_text
                response_message += f"Content for '{request.target_element_id}' directly updated. "
        else:
            llm_contextual_prompt = _build_llm_contextual_prompt(request, current_pydantic_poster)

            if llm_contextual_prompt:
                try:
                    agent = ChatAgent(system_message=BaseMessage.make_assistant_message(role_name="Poster Content Assistant", content="Provide only the new text for the field being edited."))
                    llm_response_obj = agent.step(input_message=BaseMessage.make_user_message(role_name="User", content=llm_contextual_prompt))

                    if llm_response_obj.msgs and llm_response_obj.msgs[0].content:
                        llm_generated_content_for_update = llm_response_obj.msgs[0].content.strip()
                        response_message += f"LLM response: \"{llm_generated_content_for_update}\". "
                    else:
                        response_message += "LLM produced no content update. "
                except Exception as e:
                    response_message += f"LLM service error: {str(e)}. "
            else:
                response_message += f"Error: Could not process LLM request for target '{request.target_element_id}'. "

        if llm_generated_content_for_update is not None and request.target_element_id:
            _apply_llm_update_to_payload(
                llm_generated_content_for_update,
                request.target_element_id,
                update_payload_dict,
                current_pydantic_poster
            )

    # 4. Finalize and save to DB
    if not update_payload_dict and not request.prompt_text:
        if not response_message:
            response_message = "No update action performed."
    elif not response_message and update_payload_dict:
        response_message = "Poster attributes updated."

    if update_payload_dict:
        if "sections" in update_payload_dict:
            for old_sec_orm in list(db_poster.sections):
                if old_sec_orm.image_urls:
                    for rel_path in old_sec_orm.image_urls:
                        _delete_uploaded_image_file(rel_path)
                old_section_dir = config.UPLOADED_IMAGES_DIR / f"poster_{poster_id}" / f"section_{old_sec_orm.section_id}"
                if old_section_dir.exists():
                    shutil.rmtree(old_section_dir, ignore_errors=True)

        poster_update_schema = schemas.PosterUpdate(**update_payload_dict)
        updated_db_poster = crud.update_poster_data(db=db, poster_id=poster_id, poster_update=poster_update_schema)
        if not updated_db_poster:
            raise RuntimeError("Failed to save poster updates to database.")
        db_poster = updated_db_poster

    return db_poster, response_message.strip()

def _build_llm_contextual_prompt(request: schemas.OriginalLLMPromptRequest, poster: schemas.Poster) -> str:
    """Helper function to construct the prompt for the LLM based on the target element."""
    target_id = request.target_element_id
    prompt_text = request.prompt_text

    if target_id == PosterElement.POSTER_TITLE:
        return f"You are editing the title of a poster. Current title: '{poster.title}'. User instruction: '{prompt_text}'. Respond with only the new title text."
    if target_id == PosterElement.POSTER_ABSTRACT:
        return f"You are editing the abstract of poster '{poster.title}'. Current abstract: '{poster.abstract}'. User instruction: '{prompt_text}'. Respond with only the new abstract text."
    if target_id == PosterElement.POSTER_CONCLUSION:
        return f"Editing conclusion for poster '{poster.title}'. Current: '{poster.conclusion or ''}'. Instruction: '{prompt_text}'. Respond with new text."

    if target_id and PosterElement.is_section_element(target_id):
        parts = target_id.split('_')
        if len(parts) == 3:
            sec_id, target_type = parts[1], parts[2]
            target_section_obj = next((s for s in poster.sections if s.section_id == sec_id), None)
            if target_section_obj and target_type in [PosterElement.SECTION_TITLE, PosterElement.SECTION_CONTENT]:
                field_name = "title" if target_type == "title" else "content"
                current_val = getattr(target_section_obj, f"section_{field_name}")
                return f"Editing section {field_name} for section '{target_section_obj.section_title}'. Current {field_name}: '{current_val}'. Instruction: '{prompt_text}'. Respond with new text."

    if not target_id:
        return f"Poster: '{poster.title}'. Abstract: '{poster.abstract}'. User instruction: '{prompt_text}'. Provide general suggestions."

    return ""

def _apply_llm_update_to_payload(
    content: str,
    target_id: str,
    payload: dict,
    poster: schemas.Poster
):
    """Helper to apply the LLM's generated content to the correct field in the update payload."""
    if target_id == PosterElement.POSTER_TITLE:
        payload["title"] = content
    elif target_id == PosterElement.POSTER_ABSTRACT:
        payload["abstract"] = content
    elif target_id == PosterElement.POSTER_CONCLUSION:
        payload["conclusion"] = content
    elif PosterElement.is_section_element(target_id) and "sections" not in payload:
        parts = target_id.split('_')
        if len(parts) == 3:
            sec_id, target_type = parts[1], parts[2]
            temp_sections_data = [s.dict() for s in poster.sections]
            section_updated = False
            for i, sec_data in enumerate(temp_sections_data):
                if sec_data["section_id"] == sec_id:
                    if target_type == "title":
                        temp_sections_data[i]["section_title"] = content
                    elif target_type == "content":
                        temp_sections_data[i]["section_content"] = content
                    section_updated = True
                    break
            if section_updated:
                payload["sections"] = [schemas.SectionCreate(**s) for s in temp_sections_data]