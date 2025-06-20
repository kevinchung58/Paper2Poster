from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .. import config # Assuming database is a subdir of interactive_poster_backend

# For SQLite, connect_args is not strictly needed unless doing advanced thread operations
# For other DBs like PostgreSQL, you might have other connect_args or pool settings.
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URL,
    # For SQLite, if you encounter "SQLite objects created in a thread can only be used in that same thread"
    # and are directly manipulating sessions across threads (not typical with FastAPI dependencies),
    # you might need: connect_args={"check_same_thread": False}
    # However, FastAPI's dependency injection usually handles session scoping correctly.
    echo=False # Set to True to see SQL queries in logs, good for debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def create_db_and_tables():
    # Import all modules here that define models so that
    # they will be registered properly on the metadata. Otherwise
    # you will have to import them first before calling create_db_and_tables()
    from . import models_db # Ensure models are imported before create_all
    Base.metadata.create_all(bind=engine)
    print(f"Database tables created (if they didn't exist) for DB at: {config.SQLALCHEMY_DATABASE_URL}")
