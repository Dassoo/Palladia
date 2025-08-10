import json
import sys
from pathlib import Path
from rich.console import Console
from rich.text import Text

sys.path.append(str(Path(__file__).parent.parent))

from config.loader import load_config

console = Console()

def generate_model_links():
    """Generate model links mapping and save to JSON file."""
    config = load_config(verbose=False)
    
    model_links = {}
    
    for model in config.models_config.models:
        display_name = model.display_name
        if model.link:
            model_links[display_name] = model.link
    
    # Save to docs directory for dashboard access
    output_path = Path("docs/data/json/model_links.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(model_links, f, indent=2, ensure_ascii=False)
    
    console.print(f"Generated model links mapping with {len(model_links)} entries", style="dim")
    # print(f"Saved to: {output_path}")

if __name__ == "__main__":
    generate_model_links()