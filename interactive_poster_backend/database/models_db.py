from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone # Ensure timezone awareness for defaults

from .database_setup import Base # Import Base from database_setup.py

def generate_uuid_hex():
    return uuid.uuid4().hex

class DbPoster(Base):
    __tablename__ = "posters"

    poster_id = Column(String, primary_key=True, index=True, default=generate_uuid_hex)
    title = Column(String, index=True, nullable=False) # Title should not be nullable
    abstract = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    theme = Column(String, default="default_theme", nullable=False) # This was the old general 'theme'
    selected_theme = Column(String, default="default", nullable=False) # New field for specific styling theme

    # It's good practice to use timezone-aware datetimes for database storage
    last_modified = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    pptx_file_path = Column(String, nullable=True)
    preview_image_path = Column(String, nullable=True)
    style_overrides = Column(JSON, nullable=True)
    preview_status = Column(String, default="completed", nullable=False)
    # Possible statuses: "completed", "pending", "generating", "failed"
    preview_last_error = Column(Text, nullable=True)

    # Relationship to sections
    # cascade="all, delete-orphan" means sections are deleted if the poster is deleted.
    sections = relationship("DbSection", back_populates="poster", cascade="all, delete-orphan", lazy="selectin")

class DbSection(Base):
    __tablename__ = "sections"

    section_id = Column(String, primary_key=True, index=True, default=generate_uuid_hex)
    poster_id = Column(String, ForeignKey("posters.poster_id"), nullable=False, index=True) # Added index

    section_title = Column(String, nullable=False) # Section title should not be nullable
    section_content = Column(Text, nullable=True)

    # Storing list of image URLs/placeholders as JSON string
    # SQLite handles JSON type if SQLAlchemy is recent enough and underlying SQLite supports it.
    # Otherwise, Text can be used with manual json.dumps/loads.
    # JSON type is more flexible for querying if the DB supports it directly.
    image_urls = Column(JSON, nullable=True) # Standardized name, default will be handled by Pydantic/CRUD

    poster = relationship("DbPoster", back_populates="sections")

# Note: The `lazy="selectin"` in the DbPoster.sections relationship is an optimization
# to load sections along with the poster in one go when the poster is queried,
# avoiding N+1 query problems. This requires SQLAlchemy 1.4+.
# For older versions or other preferences, "select" (default) or "joined" could be used.
