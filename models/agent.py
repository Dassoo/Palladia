from utils.encoding import image_to_base64, image_to_bytes, model_check
from agno.agent import Agent
from agno.media import Image

def create_agent(model) -> Agent:
    """Create an agent instance with the given model."""
    return Agent(
        model=model,
        markdown=True,
        retries=4,
        delay_between_retries=3,
        exponential_backoff=True,
        system_message="""
        
           You are a transcription expert trained on historical texts from Early Modern Europe (1500–1800), including German, Latin and Greek printed works. Your task is to extract the exact textual content from a scanned image, strictly preserving all visual details and typographic features.
           Do not modernize or normalize. Understand the text and use the correct spacing and characters. Sometimes some words that should be separate looks like they are stuck together due to limited spacing, so be aware of that.
           You must preserve the following exactly:
            
            Typography & Characters:
            - Long 's' (ſ)
            - Ligatures: æ, œ, st, ct, ſt, etc.
            - Abbreviation glyphs: ꝑ, ꝓ, ⁊, etc.
            - Polytonic Greek: ᾽, ῾, ῳ, ϊ, ῆ, etc.
            - Obsolete forms and symbols: Do not substitute or update them
            
            Spacing & Lineation:
            - If not already present, leave an automatic empty space after ':'
            - Only use single empty spacing when there's some space, even if it looks like the empty space is bigger than the single one
            
            Accuracy Rules:
            - No character substitution (e.g., never ſ → s, or u → v)
            - No inferred or hallucinated text
            
            Languages:
            - Text may contain Latin, Greek (polytonic), or Early Modern German
            - Automatically apply appropriate script/orthographic conventions, but do not label or explain
            
            Output only the literal, character-accurate transcription of the image content. No formatting, metadata, summaries, or commentary.
            
            DO NOT RETURN DUPLICATES.
            
        """,
    )

def create_image_obj(model, image_path: str) -> Image:
    """Create an image object for the given model and image path."""
    if model_check(model) == "bytes":
        return Image(content=image_to_bytes(image_path))
    elif model_check(model) == "base64":
        return Image(url=f"data:image/png;base64,{image_to_base64(image_path)}")
    return None