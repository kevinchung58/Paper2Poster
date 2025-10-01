from sqlalchemy.orm import Session
from sqlalchemy import func # For count
import os
import shutil
from pathlib import Path
import logging # For logging
from .. import config # To access UPLOADED_IMAGES_DIR
from . import models_db
from ..schemas import models as schemas # Pydantic schemas
import uuid
from datetime import datetime, timezone

# --- Poster CRUD Functions ---

def get_poster(db: Session, poster_id: str) -> models_db.DbPoster | None:
    """Retrieve a poster by its ID, including its sections."""
    return db.query(models_db.DbPoster).filter(models_db.DbPoster.poster_id == poster_id).first()

def get_all_posters(db: Session, skip: int = 0, limit: int = 100) -> list[models_db.DbPoster]:
    """Retrieve all posters with pagination."""
    return db.query(models_db.DbPoster).order_by(models_db.DbPoster.last_modified.desc()).offset(skip).limit(limit).all()

def create_poster(db: Session, poster_data: schemas.PosterCreate) -> models_db.DbPoster:
    """Create a new poster with its sections."""

    # Generate a UUID for the new poster
    new_poster_id = uuid.uuid4().hex

    db_poster = models_db.DbPoster(
        poster_id=new_poster_id,
        title=poster_data.title,
        abstract=poster_data.abstract,
        conclusion=poster_data.conclusion,
        theme=poster_data.theme or "default_theme",
        selected_theme=poster_data.selected_theme or "default",
        style_overrides=poster_data.style_overrides.dict(exclude_unset=True) if poster_data.style_overrides else None, # Add style_overrides
        last_modified=datetime.now(timezone.utc) # Set initial last_modified
        # pptx_file_path and preview_image_path are initially None
    )

    if poster_data.sections:
        for section_data in poster_data.sections:
            db_section = models_db.DbSection(
                section_id=uuid.uuid4().hex, # Generate ID for each new section
                poster_id=new_poster_id, # Link to the parent poster
                section_title=section_data.section_title,
                section_content=section_data.section_content,
                image_urls=section_data.image_urls # Use standardized 'image_urls'
            )
            db_poster.sections.append(db_section) # Appending to relationship handles adding to session if configured
            # db.add(db_section) # Not strictly necessary if cascade is working from poster append

    db.add(db_poster)
    db.commit()
    db.refresh(db_poster) # To get any DB-generated defaults and relationships loaded
    return db_poster

def update_poster_data(db: Session, poster_id: str, poster_update: schemas.PosterUpdate) -> models_db.DbPoster | None:
    """Update a poster's attributes and its sections."""
    db_poster = get_poster(db, poster_id)
    if not db_poster:
        return None

    # Store original sections data for comparison and cleanup
    original_sections_orm = list(db_poster.sections) # Make a copy before modification
    original_sections_map = {s.section_id: s for s in original_sections_orm}

    # Iterate over fields that were explicitly set in the Pydantic model
    for field in poster_update.__fields_set__:
        value = getattr(poster_update, field)
        if field == "sections":
            new_sections_orm_list = []
            new_section_ids_from_payload = set()

            if value is not None: # If sections are provided in payload (can be empty list)
                for section_create_data in value: # value is List[schemas.SectionCreate]
                    # This assumes SectionCreate does not have section_id, so all are new.
                    # If updating existing sections by ID was intended, SectionCreate would need section_id
                    # and we'd fetch existing or create new.
                    # Given current frontend sends full list of sections including existing ones (as SectionCreate),
                    # this effectively means replacing all sections.
                    new_section_orm = models_db.DbSection(
                        section_id=uuid.uuid4().hex,
                        poster_id=db_poster.poster_id,
                        section_title=section_create_data.section_title,
                        section_content=section_create_data.section_content,
                        image_urls=section_create_data.image_urls,
                    )
                    new_sections_orm_list.append(new_section_orm)
                    if hasattr(section_create_data, 'section_id') and section_create_data.section_id: # Should not happen with SectionCreate
                         new_section_ids_from_payload.add(section_create_data.section_id)
                    else: # For truly new sections, their generated ID won't be in old_section_ids_to_delete_dirs_for
                         pass


            # Cleanup: Delete files from sections that are removed or whose image_urls have changed
            # This logic needs to be precise. If sections are entirely replaced (identified by new IDs),
            # then all old section image directories should be removed.
            # If a section is updated (same ID, but new image_urls list), then only diff of URLs should be deleted.
            # Current logic with SectionCreate implies all sections are new, so all old ones are removed.

            # Delete files and directories of all old sections because they are being replaced
            for old_sec_orm in original_sections_orm:
                if old_sec_orm.image_urls:
                    for rel_path in old_sec_orm.image_urls:
                        _delete_uploaded_image_file(rel_path)

                old_section_dir = config.UPLOADED_IMAGES_DIR / f"poster_{poster_id}" / f"section_{old_sec_orm.section_id}"
                if old_section_dir.exists() and old_section_dir.is_dir():
                    try:
                        shutil.rmtree(old_section_dir)
                        logger.info(f"Deleted section image directory (due to section replacement): {old_section_dir}")
                    except Exception as e:
                        logger.error(f"Error deleting section image directory {old_section_dir}: {e}", exc_info=True)

            db_poster.sections = new_sections_orm_list # Assign the new list of ORM sections

        elif field == "style_overrides":
            if value is None: # Client explicitly sent "style_overrides": null
                db_poster.style_overrides = None
            else: # Client sent an object for style_overrides
                # Assuming 'value' is already a PosterElementStyles Pydantic model
                db_poster.style_overrides = value.dict(exclude_unset=True) # Store as dict
        else:
            # For other simple fields like title, abstract, selected_theme etc.
            # If value is None for a non-nullable DB field (e.g. selected_theme),
            # this could cause an IntegrityError if the DB doesn't apply its default on None.
            # For `selected_theme` (non-nullable, default "default"), if client sends `null`,
            # it's better to apply the default explicitly or disallow `null` in Pydantic schema.
            # For now, direct assignment. If `selected_theme=None` is passed for `nullable=False` field,
            # it might error. Pydantic `Optional[str]=None` allows `None`.
            # `poster_update.selected_theme` in Pydantic is `Optional[str] = None`,
            # so if client sends `null`, `value` will be `None`.
            # `DbPoster.selected_theme` is `nullable=False`. This is a potential conflict.
            # Let's handle it: if key is 'selected_theme' and value is None, use DB default.
            # However, setattr won't trigger DB default directly with None on non-nullable.
            # This logic is better handled by Pydantic schema validation or specific setter in model if complex.
            # For now, direct setattr:
            if field == "selected_theme" and value is None:
                 # Skip setting `None` to a non-nullable field if that's not desired.
                 # Or set to default. For now, if client sends null for selected_theme, it's a problem.
                 # Let's assume client won't send null for selected_theme if it means "no change".
                 # If client means "reset to default", this logic needs to be specific.
                 # The current Pydantic `selected_theme: Optional[str] = None` in PosterUpdate
                 # means it can be omitted (no change) or set to a string. Setting to `null` is not typical for reset.
                 # So, if value is not None, we set it. If it is None, and field is in __fields_set__,
                 # it means explicit null, which is an issue for non-nullable `selected_theme`.
                 # For simplicity, let's assume `value` will be a valid theme string here due to Pydantic validation.
                 pass # This pass means if selected_theme is None and in __fields_set__, it won't be updated.
                      # This is not ideal. A client sending "selected_theme": null should probably error or reset.
                      # Corrected logic: if field is set, and value is not None, update.
                      # If value is None for a non-nullable field, it's more complex.
                      # The previous loop `for key, value in update_data.items(): setattr(db_poster, key, value)`
                      # was simpler for fields guaranteed to be valid by Pydantic.
                      # Let's revert to that for simple fields and handle complex ones like style_overrides and sections separately.
            setattr(db_poster, field, value)

    # Re-applying the simpler loop for direct attributes, and handling complex types separately
    # This is because __fields_set__ logic became complicated with non-nullable fields.
    update_data_dict = poster_update.dict(exclude_unset=True)
    for key, value_from_dict in update_data_dict.items():
        if key == "sections":
            # This is now handled above if "sections" is in __fields_set__
            # To avoid double processing if we combine strategies:
            if "sections" not in poster_update.__fields_set__: # If not handled by __fields_set__ loop (e.g. if that was removed)
                # ... (section replacement logic as above) ...
                pass # This part is complex due to replacing the whole collection.
                     # The __fields_set__ approach for sections is better.
        elif key == "style_overrides":
             # Also handled by __fields_set__ loop if "style_overrides" is in __fields_set__
            if "style_overrides" not in poster_update.__fields_set__:
                if value_from_dict is None:
                    db_poster.style_overrides = None
                else: # It's a dict from poster_update.dict()
                    db_poster.style_overrides = value_from_dict
        else: # title, abstract, conclusion, theme, selected_theme
            # For selected_theme (non-nullable in DB): if value_from_dict is None, this will fail.
            # Pydantic PosterUpdate has selected_theme: Optional[str]=None.
            # This means client can send "selected_theme": null.
            # This should either be an error, or map to default.
            if key == "selected_theme" and value_from_dict is None:
                # Option 1: Raise error (better for explicit control)
                # raise ValueError("selected_theme cannot be null")
                # Option 2: Set to DB default (if known and desired)
                db_poster.selected_theme = "default" # Assuming "default" is the actual default
            else:
                setattr(db_poster, key, value_from_dict)

    # The __fields_set__ approach is cleaner. Let's stick to that and refine it.
    # Previous SEARCH block was for the loop: for key, value in update_data.items():
    # The REPLACE block should be the refined version using __fields_set__.

    # Corrected refined logic using __fields_set__ from the subtask description:
    for field in poster_update.__fields_set__: # Pydantic v1 way
        value = getattr(poster_update, field)
        if field == "sections":
            if value is not None:
                # Clear existing sections first
                db_poster.sections = []
                # db.flush() # Not strictly needed with cascade if objects are expunged or handled by session
                for section_create_data in value: # value is List[SectionCreate]
                    db_section = models_db.DbSection(
                        section_id=uuid.uuid4().hex,
                        poster_id=db_poster.poster_id,
                        **section_create_data.dict() # This should now correctly include 'image_urls'
                                                     # if SectionCreate has it and DbSection init accepts it.
                    )
                    db_poster.sections.append(db_section)
            else: # Client explicitly sent "sections": null, so clear them
                db_poster.sections = []
        elif field == "style_overrides":
            if value is None: # Client explicitly sent "style_overrides": null
                db_poster.style_overrides = None
            else: # Client sent an object for style_overrides
                db_poster.style_overrides = value.dict(exclude_unset=True)
        elif field == "selected_theme":
            if value is None:
                # This implies client sent "selected_theme": null.
                # Since DB field is non-nullable with a default, we should set it to the default.
                db_poster.selected_theme = "default" # Match DB model default
            else:
                db_poster.selected_theme = value
        else: # For other simple fields like title, abstract, conclusion, theme
            setattr(db_poster, field, value)

    # The DbPoster model's onupdate for last_modified should handle this automatically
    # db_poster.last_modified = datetime.now(timezone.utc)

    db.commit()
    db.refresh(db_poster)
    return db_poster

def update_poster_filepaths(db: Session, poster_id: str, pptx_path: str | None, preview_path: str | None) -> models_db.DbPoster | None:
    """Update file paths for a poster."""
    db_poster = get_poster(db, poster_id)
    if not db_poster:
        return None

    if pptx_path is not None:
        db_poster.pptx_file_path = pptx_path
    if preview_path is not None:
        db_poster.preview_image_path = preview_path

    # last_modified will be updated by onupdate
    db.commit()
    db.refresh(db_poster)
    return db_poster

def delete_poster(db: Session, poster_id: str) -> models_db.DbPoster | None:
    """Delete a poster, its associated sections (due to cascade), and its uploaded image files/directories."""
    db_poster = get_poster(db, poster_id)
    if db_poster:
        logger.info(f"Deleting poster {poster_id} and its associated uploaded images.")
        # Delete images and section directories
        for section in db_poster.sections: # These are DbSection ORM objects
            if section.image_urls: # This is a list of relative paths
                for rel_path in section.image_urls:
                    _delete_uploaded_image_file(rel_path)
            # Delete the specific section's image directory
            # Relative path for section dir: poster_{poster_id}/section_{section.section_id}
            # This needs to be constructed carefully. The rel_path above already contains this structure.
            # So, deleting individual files is primary. Deleting the directory structure is next.

            # Construct section directory path based on how relative_file_path_to_store was made in upload endpoint
            # relative_file_path_to_store = Path(config.UPLOADED_IMAGES_DIR_NAME) / f"poster_{poster_id}" / f"section_{section_id}" / unique_filename
            # So, the directory for a section is config.UPLOADED_IMAGES_DIR / f"poster_{poster_id}" / f"section_{section.section_id}"
            section_dir = config.UPLOADED_IMAGES_DIR / f"poster_{poster_id}" / f"section_{section.section_id}"
            if section_dir.exists() and section_dir.is_dir():
                try:
                    shutil.rmtree(section_dir)
                    logger.info(f"Deleted section image directory: {section_dir}")
                except Exception as e:
                    logger.error(f"Error deleting section image directory {section_dir}: {e}", exc_info=True)

        # Delete the poster's main image directory (e.g., uploaded_images/poster_{poster_id})
        # This will remove any other files directly under it, and the poster_id folder itself.
        poster_image_dir = config.UPLOADED_IMAGES_DIR / f"poster_{poster_id}"
        if poster_image_dir.exists() and poster_image_dir.is_dir():
            try:
                shutil.rmtree(poster_image_dir)
                logger.info(f"Deleted poster image directory: {poster_image_dir}")
            except Exception as e:
                logger.error(f"Error deleting poster image directory {poster_image_dir}: {e}", exc_info=True)

        # Now delete the poster from DB (cascades to DbSection rows)
        db.delete(db_poster)
        db.commit()
        return db_poster # Return the deleted object (now detached from session)
    return None


# --- Section CRUD Functions (if direct manipulation is needed) ---
# For now, sections are managed primarily through the Poster object.
# These can be expanded if more granular section control via API is required.

def get_section(db: Session, section_id: str) -> models_db.DbSection | None:
    """Retrieve a specific section by its ID."""
    return db.query(models_db.DbSection).filter(models_db.DbSection.section_id == section_id).first()

def update_poster_preview_status(
    db: Session,
    poster_id: str,
    status: str,
    preview_image_path: Optional[str] = None,
    error_message: Optional[str] = None
) -> models_db.DbPoster | None:
    db_poster = get_poster(db, poster_id=poster_id)
    if not db_poster:
        return None

    db_poster.preview_status = status
    if status == "completed":
        if preview_image_path is not None: # Only update if a new path is given
            db_poster.preview_image_path = preview_image_path
        db_poster.preview_last_error = None # Clear previous error on success
    elif status == "failed":
        db_poster.preview_last_error = error_message
    elif status in ["pending", "generating"]:
        db_poster.preview_last_error = None # Clear error when starting/pending
        # Optionally, clear old preview_image_path if it's now invalid
        # db_poster.preview_image_path = None

    # last_modified will be updated by ORM's onupdate if the model is touched
    db.commit()
    db.refresh(db_poster)
    return db_poster

def update_section_content(db: Session, section_id: str, content: str) -> models_db.DbSection | None:
    """Update only the content of a specific section."""
    db_section = get_section(db, section_id)
    if db_section:
        db_section.section_content = content
        # Need to update the parent poster's last_modified timestamp
        if db_section.poster:
            db_section.poster.last_modified = datetime.now(timezone.utc)
        db.commit()
        db.refresh(db_section)
        return db_section
    return None

logger = logging.getLogger(__name__)

def _delete_uploaded_image_file(relative_path: str): # Removed logger arg, use module logger
    if not relative_path or relative_path.startswith(('http://', 'https://')):
        # logger.debug(f"Skipping deletion for non-local or empty path: {relative_path}")
        return

    # Ensure relative_path does not try to escape the intended base directory
    # by resolving it against a known root and checking if it's still within that root.
    # config.UPLOADED_IMAGES_DIR is absolute. relative_path is like "poster_X/section_Y/file.png".
    # So, full_path should be config.UPLOADED_IMAGES_DIR / relative_path.

    # Check for ".." components to prevent path traversal, although Path object should handle this somewhat.
    if ".." in Path(relative_path).parts:
        logger.warning(f"Skipping deletion for potentially unsafe path: {relative_path}")
        return

    full_path = config.UPLOADED_IMAGES_DIR / relative_path
    try:
        # Resolve to prevent symbolic link traversal issues if any, though less common here.
        resolved_path = full_path.resolve()
        # Ensure the resolved path is still within the UPLOADED_IMAGES_DIR
        if config.UPLOADED_IMAGES_DIR.resolve() not in resolved_path.parents:
            logger.warning(f"Skipping deletion for path outside designated upload dir: {resolved_path}")
            return

        if resolved_path.is_file():
            resolved_path.unlink()
            logger.info(f"Deleted uploaded image file: {resolved_path}")
        # else:
            # logger.info(f"Uploaded image file not found for deletion (already deleted or invalid path): {resolved_path}")
    except Exception as e:
        logger.error(f"Error deleting uploaded image file {full_path}: {e}", exc_info=True)


# Helper for converting Pydantic Poster to DbPoster, not typically used directly in CRUD like this
# but shows mapping. CRUD functions take Pydantic models as input for create/update.
# def pydantic_poster_to_db_poster(poster: schemas.PosterCreate, existing_db_poster: models_db.DbPoster = None) -> models_db.DbPoster:
#     db_model = existing_db_poster or models_db.DbPoster(poster_id=uuid.uuid4().hex)
#     db_model.title = poster.title
#     # ... map other fields ...
#     return db_model

# Helper to convert DbPoster with sections to Pydantic Poster schema for API responses
# This is useful if you don't use .from_orm() directly in the route or want custom logic.
# However, .from_orm() is generally preferred.
# def db_poster_to_pydantic_poster(db_poster: models_db.DbPoster) -> schemas.Poster:
#     return schemas.Poster.from_orm(db_poster)
