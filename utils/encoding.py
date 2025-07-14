from agno.models.google import Gemini
from agno.models.anthropic import Claude
import base64

def model_check(model) -> str:
    """Check if the model is Gemini or Claude for the image encoding."""
    if isinstance(model, Gemini) or isinstance(model, Claude):
        return "bytes"
    else:
        return "base64"

def image_to_base64(image_path: str) -> str:
    """Convert an image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def image_to_bytes(image_path: str) -> bytes:
    """Convert an image to bytes."""
    with open(image_path, "rb") as image_file:
        return image_file.read()