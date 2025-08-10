import json
import os
import subprocess
from pathlib import Path
from typing import Dict

import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.loader import load_config

def get_model_name_mapping() -> Dict[str, str]:
    """Get mapping from raw model IDs to standardized names."""
    config = load_config(verbose=False)
    mapping = {}
    
    for model in config.models_config.models:
        if model.standard_name:
            mapping[model.id] = model.standard_name
        else:
            mapping[model.id] = model.id
    
    return mapping

def find_all_json_files(base_path: Path) -> list[Path]:
    """Find all JSON files in the directory tree, excluding manifest.json."""
    json_files = []
    
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.json') and file != 'manifest.json':
                json_files.append(Path(root) / file)
    
    return json_files



def update_json_file(file_path: Path, name_mapping: Dict[str, str]) -> int:
    """Update a single JSON file to use standardized model names. Returns number of changes made."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            return 0
        
        changes = 0
        new_data = {}
        
        for key, value in data.items():
            if key in name_mapping and name_mapping[key] != key:
                new_data[name_mapping[key]] = value
                changes += 1
            else:
                new_data[key] = value
        
        if changes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=4, ensure_ascii=False)
        
        return changes
        
    except Exception:
        return 0

def main():
    name_mapping = get_model_name_mapping()
    
    # Find all JSON files
    base_path = Path('docs/data/json')
    if not base_path.exists():
        print(f"Error: Directory not found: {base_path}")
        return 1
    
    json_files = find_all_json_files(base_path)
    
    total_files = len(json_files)
    modified_files = 0
    total_changes = 0
    
    for file_path in json_files:
        changes = update_json_file(file_path, name_mapping)
        if changes > 0:
            modified_files += 1
            total_changes += changes
    
    # Update model links if changes were made
    if total_changes > 0:
        try:
            subprocess.run([sys.executable, str(Path(__file__).parent / "generate_model_links.py")], check=True)
        except Exception as e:
            print(f"Warning: Could not update model links: {e}")
    
    print(f"Update Summary:")
    print(f"  Files processed: {total_files}")
    print(f"  Files modified: {modified_files}")
    print(f"  Total changes: {total_changes}")
    
    return 0

if __name__ == "__main__":
    main()