import json
import os
from pathlib import Path
from typing import Any, Dict


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
    file_path = Path("results") / path.parent / f"{path.stem}.json"
    
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


def to_json_avg(model_id: str, avg_wer: float, avg_cer: float, 
               avg_accuracy: float, avg_exec_time: float, 
               source: str, total_images: int):
    """Save average metrics for a model across multiple images.
    
    Args:
        model_id: Identifier for the model
        avg_wer: Average Word Error Rate
        avg_cer: Average Character Error Rate
        avg_accuracy: Average accuracy
        avg_exec_time: Average execution time in seconds
        source: Source identifier for the evaluation
        total_images: Total number of images processed
    """
    file_path = f"results/{source}.json"
    data = {
        model_id: {
            "source": source,
            "images": total_images,
            "avg_wer": avg_wer * 100,
            "avg_cer": avg_cer * 100,
            "avg_accuracy": avg_accuracy * 100,
            "avg_time": avg_exec_time
        }
    }
    _save_to_json(file_path, data)