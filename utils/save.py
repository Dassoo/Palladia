import json
import os
from pathlib import Path
from typing import Any, Dict
from collections import defaultdict

from rich.console import Console
console = Console()

def _save_to_json(file_path: str, data: Dict[str, Any]) -> None:
    """Helper function to save data to JSON file.
    
    Args:
        file_path: Path to the JSON file
        data: Dictionary containing the data to save
    """
    os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            existing_data = json.load(f)
        existing_data.update(data)
        data = existing_data
    
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def to_json(model, gt: str, response, wer: float, cer: float, 
           accuracy: float, exec_time: float, image_path: str) -> None:
    """Save individual image evaluation results.
    
    Args:
        model: The model used for evaluation
        gt: Ground truth text
        response: Model response object
        wer: Word Error Rate
        cer: Character Error Rate
        accuracy: Accuracy score
        exec_time: Execution time in seconds
        image_path: Path to the evaluated image (e.g., 'GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/00001.bin.png')
    """
    path = Path(image_path)
    file_path = Path("docs/json") / path.parent / f"{path.stem}.json"
    
    data = {
        model.id: {
            "gt": gt,
            "response": response.content,
            "wer": wer * 100,
            "cer": cer * 100,
            "accuracy": accuracy * 100,
            "time": exec_time
        }
    }
    _save_to_json(file_path, data)


def aggregate_folder_results(folder_path: str) -> Dict[str, Any]:
    """Manually aggregate results from all JSON files in a folder and calculate average metrics per model.
    
    Args:
        folder_path: Path to folder containing JSON files (e.g., 'docs/json/GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius')
    
    Returns:
        Dictionary with aggregated results per model
    """
    folder_path = Path(folder_path)
    
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    # Collect all metrics per model
    model_metrics = defaultdict(lambda: {
        'wer': [],
        'cer': [],
        'accuracy': [],
        'time': []
    })
    
    # Read all JSON files in the folder
    json_files = list(folder_path.glob("*.json"))
    
    if not json_files:
        raise ValueError(f"No JSON files found in {folder_path}")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Extract metrics for each model in this file
            for model_id, metrics in data.items():
                if isinstance(metrics, dict) and all(key in metrics for key in ['wer', 'cer', 'accuracy', 'time']):
                    model_metrics[model_id]['wer'].append(metrics['wer'])
                    model_metrics[model_id]['cer'].append(metrics['cer'])
                    model_metrics[model_id]['accuracy'].append(metrics['accuracy'])
                    model_metrics[model_id]['time'].append(metrics['time'])
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Skipping invalid JSON file {json_file}: {e}")
            continue
    
    if not model_metrics:
        raise ValueError(f"No valid model metrics found in {folder_path}")
    
    # Calculate averages for each model
    aggregated_results = {}
    
    # Extract source path from folder structure
    source_path = str(folder_path)
    if source_path.startswith('docs/json/'):
        source_path = source_path[10:]  # Remove 'docs/json/' prefix
    
    for model_id, metrics in model_metrics.items():
        if metrics['wer']:  # Ensure we have data
            aggregated_results[model_id] = {
                "source": source_path,
                "images": len(metrics['wer']),
                "avg_wer": sum(metrics['wer']) / len(metrics['wer']),
                "avg_cer": sum(metrics['cer']) / len(metrics['cer']),
                "avg_accuracy": sum(metrics['accuracy']) / len(metrics['accuracy']),
                "avg_time": sum(metrics['time']) / len(metrics['time'])
            }
    
    output_file = f"{folder_path}.json"
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(aggregated_results, f, indent=4)
    
    console.print(f"\nAggregated results saved to: {output_file}", style="dim")
    console.print(f"Processed {len(json_files)} json files, found {len(aggregated_results)} models", style="dim")
    
    return aggregated_results


if __name__ == "__main__":
    # Manual example usage if needed
    aggregate_folder_results('docs/json/GT4HistOCR/corpus/EarlyModernLatin/1564-Thucydides-Valla')