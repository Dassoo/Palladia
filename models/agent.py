from utils.encoding import image_to_base64, image_to_bytes, model_check
from agno.agent import Agent
from agno.media import Image

def create_agent(model):
    """Create an agent instance with the given model."""
    return Agent(
        model=model,
        markdown=True,
        system_message="You are an expert text analyzer. Only return the accurate textual content of the image. Keep the original symbols and spacing, don't add or substitute any characters. Keep in mind that the text is in Early Modern Latin and Greek, so use the correct characters. Do not hallucinate or approximate, check every single character accurately. For example, don't substitute 'ſ' with 's' or 'f'. Keep the original symbols and characters.",
    )

def create_image_obj(model, image_path: str):
    """Create an image object for the given model and image path."""
    if model_check(model) == "bytes":
        return Image(content=image_to_bytes(image_path))
    elif model_check(model) == "base64":
        return Image(url=f"data:image/png;base64,{image_to_base64(image_path)}")
    return None