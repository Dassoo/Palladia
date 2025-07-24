#!/usr/bin/env python3
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
    
    # Ensure structure exists
    if "structure" not in manifest:
        manifest["structure"] = {}
    
    # Ensure files exists
    if "files" not in manifest:
        manifest["files"] = []
    
    # Add second-last part to structure if not existing
    if second_last_part not in manifest["structure"]:
        manifest["structure"][second_last_part] = []
    
    # Add final part (without .json) to structure array if not existing
    if final_part not in manifest["structure"][second_last_part]:
        manifest["structure"][second_last_part].append(final_part)
    
    # Add final part (with .json) to files array if not existing
    json_filename = f"{final_part}.json"
    if json_filename not in manifest["files"]:
        manifest["files"].append(json_filename)
    
    # Update generated timestamp
    manifest["generated"] = datetime.now().isoformat()
    
    # Save updated manifest
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # print(f"Manifest updated successfully!")
