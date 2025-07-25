import json
import os
from pathlib import Path
from datetime import datetime


def update_manifest(input_path):
    """
    Update the manifest.json file based on the input_path.
    
    Args:
        input_path: Path like 'GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius'
    """
    
    # Get the final part and second-last part
    final_part = os.path.basename(input_path)  # '1471-Orthographia-Tortellius'
    second_last_part = os.path.basename(os.path.dirname(input_path))  # 'EarlyModernLatin'
    
    # Path to manifest file
    manifest_path = "docs/json/manifest.json"
    
    # Load existing manifest or create new one
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "description": "Auto-generated manifest of all available JSON files based on GT4HistOCR corpus structure",
            "generated": datetime.now().isoformat(),
            "structure": {},
            "files": []
        }
    
    # Update and save new manifest
    if "structure" not in manifest:
        manifest["structure"] = {}
    if "files" not in manifest:
        manifest["files"] = []

    if second_last_part not in manifest["structure"]:
        manifest["structure"][second_last_part] = []
    
    if final_part not in manifest["structure"][second_last_part]:
        manifest["structure"][second_last_part].append(final_part)
    
    # Create the full nested path for the JSON file
    json_filepath = f"GT4HistOCR/corpus/{second_last_part}/{final_part}.json"
    if json_filepath not in manifest["files"]:
        manifest["files"].append(json_filepath)
    
    manifest["generated"] = datetime.now().isoformat()
    
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # print(f"Manifest updated successfully!")
