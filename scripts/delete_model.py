import json
import os
import glob
import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.update_manifest import regenerate_full_manifest
from evaluation.graph import create_graph


def delete_model_from_file(file_path: str, model_name: str) -> bool:
    """
    Delete a model from a single JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if model_name in data:
            del data[model_name]
            
            # Write back the updated data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            print(f"Removed {model_name} from {file_path}")
            return True
        else:
            return False
            
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error processing {file_path}: {e}")
        return False


def find_all_json_files(base_path: str = "docs/json") -> List[str]:
    """
    Find all JSON files in the evaluation directory structure.
    """
    json_files = []
    
    # Find all JSON files recursively, excluding manifest.json
    for json_file in glob.glob(f"{base_path}/**/*.json", recursive=True):
        if not json_file.endswith("manifest.json"):
            json_files.append(json_file)
    
    return json_files


def delete_model_from_all_evaluations(model_name: str, base_path: str = "docs/json") -> Dict[str, Any]:
    """
    Delete a model from all evaluation JSON files.
    """
    print(f"Starting deletion of model: {model_name}")
    print("=" * 50)
    
    # Find all JSON files
    json_files = find_all_json_files(base_path)
    
    stats = {
        "model_name": model_name,
        "files_processed": 0,
        "files_modified": 0,
        "files_with_errors": 0,
        "modified_files": [],
        "aggregated_files": []
    }
    
    # Process each JSON file
    for json_file in json_files:
        stats["files_processed"] += 1
        
        try:
            if delete_model_from_file(json_file, model_name):
                stats["files_modified"] += 1
                stats["modified_files"].append(json_file)
                
                # Check if this is an aggregated file (not in a subdirectory with individual files)
                if not os.path.basename(json_file).startswith(('0', '1', '2')):
                    stats["aggregated_files"].append(json_file)
                    
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            stats["files_with_errors"] += 1
    
    print("\n" + "=" * 50)
    print(f"Deletion Summary:")
    print(f"   Model: {model_name}")
    print(f"   Files processed: {stats['files_processed']}")
    print(f"   Files modified: {stats['files_modified']}")
    print(f"   Files with errors: {stats['files_with_errors']}")
    print(f"   Aggregated files affected: {len(stats['aggregated_files'])}")
    
    if stats["files_modified"] > 0:
        print(f"\nUpdating manifest and regenerating graphs...")
        
        # Update manifest
        try:
            regenerate_full_manifest()
            print("Manifest updated successfully")
        except Exception as e:
            print(f"Error updating manifest: {e}")
        
        for aggregated_file in stats["aggregated_files"]:
            create_graph(aggregated_file)
            print(f"Graph created for {aggregated_file}")
        
    return stats


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python delete_model.py <model_name>")
        print("Example: python delete_model.py 'mistral-small-2506'")
        # print("Example: uv run delete_model.py 'mistral-small-2506'")
        sys.exit(1)
    
    model_name = sys.argv[1]
    result = delete_model_from_all_evaluations(model_name)
    
    if result["files_modified"] == 0:
        print(f"\nModel '{model_name}' was not found in any evaluation files.")
    else:
        print(f"\nSuccessfully deleted '{model_name}' from {result['files_modified']} files.")


def delete_model(model_name: str) -> Dict[str, Any]:
    """
    Convenience function to delete a model and update everything.
    """
    return delete_model_from_all_evaluations(model_name)