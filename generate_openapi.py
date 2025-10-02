import json
import os
from interactive_poster_backend.main import app

def generate_openapi_spec():
    """
    Generates the OpenAPI specification from the FastAPI app
    and saves it to a file in the project root.
    """
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(project_root, "openapi.json")

    # Generate the OpenAPI schema
    openapi_schema = app.openapi()

    # Write the schema to the file
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"✅ OpenAPI specification successfully generated at: {output_path}")

if __name__ == "__main__":
    generate_openapi_spec()