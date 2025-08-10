from evaluation.graph import create_graph

import json
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.text import Text

console = Console()

def scan_individual_files(subcategory_path):
    """
    Scan for individual JSON files in a subcategory folder.
    
    Args:
        subcategory_path: Path like 'docs/data/json/GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius'
    
    Returns:
        List of individual file paths relative to docs/data/json/
    """
    individual_files = []
    
    if os.path.exists(subcategory_path):
        for file in os.listdir(subcategory_path):
            if file.endswith('.json'):
                # Create path relative to docs/data/json/
                relative_path = os.path.relpath(
                    os.path.join(subcategory_path, file), 
                    'docs/json'
                )
                individual_files.append(relative_path)
    
    return sorted(individual_files)


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
    manifest_path = "docs/data/json/manifest.json"
    
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

    # Initialize category structure if needed
    if second_last_part not in manifest["structure"]:
        manifest["structure"][second_last_part] = {}
    
    # Create the full nested path for the aggregated JSON file
    json_filepath = f"GT4HistOCR/corpus/{second_last_part}/{final_part}.json"
    
    # Scan for individual files in the subcategory folder
    subcategory_path = f"docs/data/json/GT4HistOCR/corpus/{second_last_part}/{final_part}"
    individual_files = scan_individual_files(subcategory_path)
    
    # Update structure with enhanced format
    manifest["structure"][second_last_part][final_part] = {
        "aggregated": json_filepath,
        "individual_files": individual_files,
        "image_count": len(individual_files)
    }
    
    # Add aggregated file to files list (maintain backward compatibility)
    if json_filepath not in manifest["files"]:
        manifest["files"].append(json_filepath)
    
    manifest["generated"] = datetime.now().isoformat()
    
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # print(f"Manifest updated successfully!")


def regenerate_full_manifest():
    """
    Regenerate the complete manifest by scanning all existing data.
    This is useful for updating the manifest structure after changes.
    """
    manifest_path = "docs/data/json/manifest.json"
    base_path = "docs/data/json/GT4HistOCR/corpus"
    
    if not os.path.exists(base_path):
        console.print(f"Base path {base_path} does not exist", style="red")
        return
    
    manifest = {
        "description": "Auto-generated manifest of all available JSON files based on GT4HistOCR corpus structure",
        "generated": datetime.now().isoformat(),
        "structure": {},
        "files": []
    }
    
    # Scan all categories and subcategories
    for category in os.listdir(base_path):
        category_path = os.path.join(base_path, category)
        if not os.path.isdir(category_path):
            continue
            
        manifest["structure"][category] = {}
        
        for item in os.listdir(category_path):
            item_path = os.path.join(category_path, item)
            
            # Check if this is a subcategory with an aggregated JSON file
            aggregated_file = f"{item}.json"
            aggregated_path = os.path.join(category_path, aggregated_file)
            
            if os.path.exists(aggregated_path):
                # This is a subcategory with results
                json_filepath = f"GT4HistOCR/corpus/{category}/{aggregated_file}"
                create_graph("docs/data/json/" + json_filepath)
                
                # Scan for individual files
                individual_files = scan_individual_files(item_path) if os.path.isdir(item_path) else []
                
                # Add to structure
                manifest["structure"][category][item] = {
                    "aggregated": json_filepath,
                    "individual_files": individual_files,
                    "image_count": len(individual_files)
                }
                
                # Add to files list for backward compatibility
                if json_filepath not in manifest["files"]:
                    manifest["files"].append(json_filepath)
    
    # Save the regenerated manifest
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    console.print(f"Full manifest regenerated with {len(manifest['files'])} aggregated files", style="dim")
    total_individual = sum(
        len(subcategory.get('individual_files', [])) 
        for category in manifest['structure'].values() 
        for subcategory in category.values()
    )
    console.print(f"Found {total_individual} individual image files", style="dim")


if __name__ == "__main__":
    # Regenerate the full manifest with direct run
    regenerate_full_manifest()
