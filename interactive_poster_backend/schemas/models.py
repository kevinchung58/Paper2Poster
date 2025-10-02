from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# ===================================================================
# Core Data Schemas (Mirrors the database structure)
# ===================================================================

class ElementStyleProperties(BaseModel):
    """Defines style properties for a single poster element."""
    font_size: Optional[int] = None
    color: Optional[str] = None  # e.g., "#FF0000"
    font_family: Optional[str] = None

    model_config = ConfigDict(extra='forbid')

class PosterElementStyles(BaseModel):
    """Container for all overridable style elements on a poster."""
    title: Optional[ElementStyleProperties] = None
    abstract: Optional[ElementStyleProperties] = None
    conclusion: Optional[ElementStyleProperties] = None
    section_title: Optional[ElementStyleProperties] = None
    section_content: Optional[ElementStyleProperties] = None
    slide_background: Optional[str] = None

    model_config = ConfigDict(extra='forbid')

class SectionBase(BaseModel):
    """Base schema for a poster section."""
    section_id: str
    section_title: str
    section_content: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)

class PosterBase(BaseModel):
    """Base schema for a poster."""
    poster_id: str
    title: str
    abstract: Optional[str] = None
    conclusion: Optional[str] = None
    selected_theme: str = "default"
    last_modified: datetime
    pptx_file_path: Optional[str] = None
    preview_image_path: Optional[str] = None
    style_overrides: Optional[PosterElementStyles] = None
    preview_status: str = "pending"
    preview_last_error: Optional[str] = None

    # Deprecated field, kept for now for compatibility if needed, but should be phased out.
    theme: str = "default_theme"

class Section(SectionBase):
    """Full schema for a section, used for reading from DB."""
    model_config = ConfigDict(from_attributes=True)

class Poster(PosterBase):
    """Full schema for a poster including its sections."""
    sections: List[Section] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

# ===================================================================
# Schemas for Database Operations (Create/Update)
# ===================================================================

class SectionCreate(BaseModel):
    """Schema for creating a new section."""
    section_title: str
    section_content: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)

class PosterCreate(BaseModel):
    """Schema for creating a new poster in the database."""
    title: str
    abstract: Optional[str] = None
    conclusion: Optional[str] = None
    selected_theme: Optional[str] = "default"
    style_overrides: Optional[PosterElementStyles] = None
    sections: List[SectionCreate] = Field(default_factory=list)

class PosterUpdate(BaseModel):
    """Schema for updating an existing poster. All fields are optional."""
    title: Optional[str] = None
    abstract: Optional[str] = None
    conclusion: Optional[str] = None
    selected_theme: Optional[str] = None
    style_overrides: Optional[PosterElementStyles] = None
    preview_status: Optional[str] = None
    preview_last_error: Optional[str] = None
    sections: Optional[List[SectionCreate]] = None

# ===================================================================
# Schemas for API Endpoints (Request/Response)
# ===================================================================

# --- Request Schemas ---

class OriginalCreatePosterRequest(BaseModel):
    """Request body for creating a new poster session."""
    topic: Optional[str] = None
    template_id: Optional[str] = None # Currently unused, but kept for future API evolution

class OriginalLLMPromptRequest(BaseModel):
    """Request body for the main /prompt endpoint."""
    prompt_text: Optional[str] = None
    target_element_id: Optional[str] = None
    selected_theme: Optional[str] = None
    style_overrides: Optional[PosterElementStyles] = None
    is_direct_update: bool = False
    sections: Optional[List[SectionCreate]] = None

# --- Response Schemas ---

class APICreatePosterResponse(BaseModel):
    """Response for a successful poster creation."""
    poster_id: str
    poster_data: Poster
    preview_image_url: str

class APILLMPromptResponse(BaseModel):
    """Response for a successful prompt submission."""
    poster_id: str
    llm_response_text: str
    updated_poster_data: Poster
    preview_image_url: str

class APIGeneratePPTXResponse(BaseModel):
    """Response for a successful PPTX generation trigger."""
    poster_id: str
    download_url: str
    message: str