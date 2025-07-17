from utils.encoding import image_to_base64, image_to_bytes, model_check
from agno.agent import Agent
from agno.media import Image

def create_agent(model) -> Agent:
    """Create an agent instance with the given model."""
    return Agent(
        model=model,
        markdown=True,
        retries=5,
        delay_between_retries=2,
        exponential_backoff=True,
        system_message="""
        
            You are an expert historical text analyst and character-preserving transcription specialist. Your task is to extract the exact textual content from the image, maintaining absolute fidelity to the source.
            Carefully preserve all original symbols, characters, ligatures, diacritics, spacing, and punctuation. Do not modernize, normalize, or interpret characters in any way.
            The text may include Early Modern Latin, Greek (using polytonic orthography), or Early Modern German, and may feature historical glyphs such as:
            - Long s (ſ)
            - Ligatures (e.g., æ, œ, ꝑ, ꝓ, Ͳ, ϗ)
            - Tironian et (⁊)
            - Greek breathing marks, iota subscripts, and accentuation (e.g., ᾽, ῾, ῳ, ἄ)
            - Special punctuation (e.g., Greek question mark ';', ano teleia '·')
            
            Do not substitute or "correct" characters:
            For example, do not replace ſ with s, or ϗ with και. Each glyph must be rendered exactly as seen.
            Output only the precise textual content from the image — no explanations, metadata, translations, or summaries. Validate each character visually and contextually with scholarly-level accuracy.
            
        """,
    )

def create_image_obj(model, image_path: str) -> Image:
    """Create an image object for the given model and image path."""
    if model_check(model) == "bytes":
        return Image(content=image_to_bytes(image_path))
    elif model_check(model) == "base64":
        return Image(url=f"data:image/png;base64,{image_to_base64(image_path)}")
    return None