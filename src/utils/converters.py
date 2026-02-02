import base64
from pathlib import Path

def convert_to_b64(image_path: Path) -> str:
    """
    Convert an image file to base64 encoding.
    
    Args:
        image_path: Path to the image file to convert
        
    Returns:
        Base64 encoded string of the image content
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')
    

# def convert_to_b64(buffer):
#     buffer.seek(0)
#     return base64.b64encode(buffer.read()).decode()
