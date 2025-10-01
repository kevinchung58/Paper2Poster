import os
import subprocess
from pathlib import Path # For type hinting if output_dir is Path
from .. import config # Import the config

# TEMP_PREVIEWS_DIR defined in config is now the source of truth
from sqlalchemy.orm import Session # For type hinting, new session created in task
from ..database import crud
from ..database.database_setup import SessionLocal # To create a new DB session

def convert_pptx_to_png_soffice(pptx_path: str | Path, output_dir: str | Path) -> str | None:
    """
    Converts the first slide of a PPTX file to a PNG image using LibreOffice soffice.

    Args:
        pptx_path: Path to the input PPTX file.
        output_dir: Directory where the PNG should be saved.

    Returns:
        Path to the generated PNG file, or None if conversion failed.
    """
    if not os.path.exists(pptx_path):
        print(f"Error: PPTX file not found at {pptx_path}")
        return None

    # Ensure output directory exists
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            print(f"Error creating output directory {output_dir}: {e}")
            return None

    # soffice command for converting to PNG (first page only for preview)
    # For converting all slides, remove `--convert-to png:"impress_png_Export"` and just use `png`
    # and then handle multiple output files if needed. For a preview, first slide is usually enough.
    # The filter "impress_png_Export" with "PageRange=1" can be used for specific pages,
    # but soffice CLI for page range can be tricky. Simpler to get the first page by default.
    # The output filename will match the input filename.
    cmd = [
        config.SOFFICE_COMMAND, # Use configured command
        "--headless",
        "--convert-to",
        "png", # Output format
        "--outdir",
        str(output_dir), # Ensure output_dir is string for subprocess
        str(pptx_path),  # Ensure pptx_path is string for subprocess
    ]

    try:
        print(f"Executing command: {' '.join(cmd)}")
        process = subprocess.run(cmd, capture_output=True, text=True, timeout=30) # Added timeout

        if process.returncode != 0:
            print(f"Error during PPTX to PNG conversion (soffice):")
            print(f"  Return Code: {process.returncode}")
            print(f"  Stdout: {process.stdout}")
            print(f"  Stderr: {process.stderr}")
            return None
        else:
            print(f"Soffice conversion successful for {pptx_path}.")
            # Construct the expected PNG filename
            base_filename = os.path.splitext(os.path.basename(pptx_path))[0]
            expected_png_path = os.path.join(output_dir, f"{base_filename}.png")

            if os.path.exists(expected_png_path):
                print(f"Generated PNG found at: {expected_png_path}")
                return expected_png_path
            else:
                # Soffice might sometimes have quirks with output names or not produce output
                # despite a zero return code if the input file is problematic or soffice itself has issues.
                print(f"Error: Soffice reported success, but PNG file not found at {expected_png_path}.")
                print(f"  Stdout: {process.stdout}") # Log stdout as well, it might contain info
                print(f"  Stderr: {process.stderr}")
                # Check if any PNG was created in the output directory
                files_in_outdir = os.listdir(output_dir)
                png_files = [f for f in files_in_outdir if f.lower().endswith(".png") and base_filename in f]
                if png_files:
                    print(f"Found other PNG files that might match: {png_files}. Taking the first one.")
                    return os.path.join(output_dir, png_files[0])
                return None

    except subprocess.TimeoutExpired:
        print(f"Error: Soffice command timed out for {pptx_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during soffice execution: {e}")
        return None
