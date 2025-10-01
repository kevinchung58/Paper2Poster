import os
import time
from pathlib import Path
import logging

# Configure basic logging for this module
# This will allow seeing logs from this module if the main app also configures logging
# or if this module is run standalone for testing.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_old_files(directory: Path, days_to_keep: int):
    """
    Deletes files in the specified directory older than a certain number of days.

    Args:
        directory (Path): The absolute path to the directory to clean up.
        days_to_keep (int): The maximum age of files (in days) to keep.
    """
    if not isinstance(directory, Path):
        logger.error(f"Cleanup failed: 'directory' must be a Path object. Got: {type(directory)}")
        return

    if not directory.is_dir():
        # This might happen if create_temp_dirs hasn't run or failed.
        # The create_temp_dirs in main.py's startup should prevent this normally.
        logger.warning(f"Cleanup skipped: Directory '{directory}' does not exist or is not a directory.")
        return

    logger.info(f"Starting cleanup for directory: '{directory}'. Keeping files newer than {days_to_keep} days.")

    try:
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        files_deleted_count = 0
        files_failed_count = 0
        items_scanned = 0

        for item in directory.iterdir():
            items_scanned += 1
            try:
                if item.is_file():  # Only process files
                    file_mod_time = item.stat().st_mtime
                    if file_mod_time < cutoff_time:
                        item.unlink()  # Delete the file
                        logger.info(f"Deleted old file: {item}")
                        files_deleted_count += 1
                # Optionally, could add logic here to remove old empty subdirectories if they were expected
            except Exception as e:
                logger.error(f"Failed to process or delete file '{item}': {e}")
                files_failed_count += 1

        logger.info(f"Cleanup finished for '{directory}'. Scanned: {items_scanned} items. Files deleted: {files_deleted_count}. Failures: {files_failed_count}.")

    except Exception as e:
        logger.error(f"An error occurred during the cleanup process for directory '{directory}': {e}")

if __name__ == '__main__':
    # Example usage for testing the cleanup function directly
    print("Running cleanup utility directly for testing...")

    # Create dummy config values for testing
    class DummyConfig:
        APP_ROOT_DIR = Path(__file__).resolve().parent.parent
        TEMP_POSTERS_DIR = APP_ROOT_DIR / "temp_posters_test"
        TEMP_PREVIEWS_DIR = APP_ROOT_DIR / "temp_previews_test"
        DAYS_TO_KEEP_TEMP_FILES = 1 # Keep for 1 day for easier testing

    cfg = DummyConfig()

    # Ensure test directories exist
    os.makedirs(cfg.TEMP_POSTERS_DIR, exist_ok=True)
    os.makedirs(cfg.TEMP_PREVIEWS_DIR, exist_ok=True)

    print(f"Test posters directory: {cfg.TEMP_POSTERS_DIR}")
    print(f"Test previews directory: {cfg.TEMP_PREVIEWS_DIR}")

    # Create some dummy files for testing
    # New file (should be kept)
    (cfg.TEMP_POSTERS_DIR / "new_poster.pptx").write_text("new poster data")
    (cfg.TEMP_PREVIEWS_DIR / "new_preview.png").write_text("new preview data")

    # Old file (should be deleted)
    old_poster_path = cfg.TEMP_POSTERS_DIR / "old_poster.pptx"
    old_poster_path.write_text("old poster data")
    two_days_ago = time.time() - (2 * 24 * 60 * 60)
    os.utime(old_poster_path, (two_days_ago, two_days_ago))

    old_preview_path = cfg.TEMP_PREVIEWS_DIR / "old_preview.png"
    old_preview_path.write_text("old preview data")
    os.utime(old_preview_path, (two_days_ago, two_days_ago))

    print("\nBefore cleanup:")
    print(f"Posters: {[item.name for item in cfg.TEMP_POSTERS_DIR.iterdir()]}")
    print(f"Previews: {[item.name for item in cfg.TEMP_PREVIEWS_DIR.iterdir()]}")

    # Run cleanup
    cleanup_old_files(cfg.TEMP_POSTERS_DIR, cfg.DAYS_TO_KEEP_TEMP_FILES)
    cleanup_old_files(cfg.TEMP_PREVIEWS_DIR, cfg.DAYS_TO_KEEP_TEMP_FILES)

    print("\nAfter cleanup:")
    print(f"Posters: {[item.name for item in cfg.TEMP_POSTERS_DIR.iterdir()]}")
    print(f"Previews: {[item.name for item in cfg.TEMP_PREVIEWS_DIR.iterdir()]}")

    # Basic assertion for testing
    assert not old_poster_path.exists(), "Old poster was not deleted"
    assert not old_preview_path.exists(), "Old preview was not deleted"
    assert (cfg.TEMP_POSTERS_DIR / "new_poster.pptx").exists(), "New poster was incorrectly deleted"
    assert (cfg.TEMP_PREVIEWS_DIR / "new_preview.png").exists(), "New preview was incorrectly deleted"
    print("\nTest assertions passed if no errors shown above.")
