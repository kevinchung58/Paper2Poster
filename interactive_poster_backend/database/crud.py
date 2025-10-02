from typing import Optional
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
    """
    Updates a poster's data in the database.
    This function now ONLY handles database operations.
    File system operations (like cleanup) are handled by the service layer.
    """
    db_poster = get_poster(db, poster_id)
    if not db_poster:
        return None

    update_data = poster_update.dict(exclude_unset=True)

    # Handle section replacement purely at the DB level
    if "sections" in update_data:
        # This replaces the entire collection of sections for the poster.
        # SQLAlchemy will automatically handle deleting the old sections
        # from the DB due to the cascade="all, delete-orphan" setting on the relationship.
        new_sections_data = update_data.pop("sections")
        db_poster.sections = [
            models_db.DbSection(
                section_id=uuid.uuid4().hex,
                poster_id=db_poster.poster_id,
                **section_data
            ) for section_data in new_sections_data
        ]

    # Handle style overrides
    if "style_overrides" in update_data:
        style_value = update_data.pop("style_overrides")
        if style_value is None:
            db_poster.style_overrides = None
        else:
            db_poster.style_overrides = style_value

    # Update remaining simple fields
    for key, value in update_data.items():
        setattr(db_poster, key, value)

    # The 'last_modified' timestamp is handled by the ORM 'onupdate' event.
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
