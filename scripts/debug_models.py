import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.model_utils import to_eval
from config.loader import load_config

# Check what the config loader sees
try:
    app_config = load_config(verbose=True)
    print(f"\nEnabled models from config:")
    for model in app_config.enabled_models:
        display_name = model.display_name
        print(f"  - {model.provider}/{display_name} (ID: {model.id}, API key: {model.api_key_env})")
except Exception as e:
    print(f"Config loading error: {e}")

print(f"\nDEBUG: Loaded Models")
print(f"Number of models in to_eval: {len(to_eval)}")

for i, model in enumerate(to_eval):
    print(f"{i+1}. Model ID: {model.id}")
    print(f"   Model Type: {type(model).__name__}")
    print(f"   Model Attributes: {vars(model)}")
    print()

if not to_eval:
    print("No models loaded!")
else:
    print(f"{len(to_eval)} models loaded successfully")