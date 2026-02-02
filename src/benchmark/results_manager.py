import json
from datetime import datetime
from pathlib import Path
from typing import Any


def get_benchmark_path(image_path: Path, benchmarks_root: Path = Path("benchmarks")) -> Path:
    """
    Convert an image path to its corresponding benchmark directory path.
    
    Example:
        image_path: GT4HistOCR/corpus/EarlyModernLatin/1564-Thucydides-Valla/image.png
        returns: benchmarks/GT4HistOCR/corpus/EarlyModernLatin/1564-Thucydides-Valla
    """
    if image_path.is_absolute():
        relative_path = image_path
    else:
        relative_path = image_path
    
    benchmark_dir = benchmarks_root / relative_path.parent
    return benchmark_dir


def get_result_filename(image_path: Path) -> str:
    """
    Get the JSON result filename for an image.
    
    Example:
        image.png -> image.json
        image.bin.png -> image.bin.json
    """
    stem = image_path.stem
    return f"{stem}.json"


def load_existing_results(image_path: Path, benchmarks_root: Path = Path("benchmarks")) -> dict[str, Any]:
    """
    Load existing results for an image if they exist.
    
    Args:
        image_path: Path to the image
        benchmarks_root: Root directory for all benchmarks
        
    Returns:
        The existing results dict if found, or an empty dict
    """
    benchmark_dir = get_benchmark_path(image_path, benchmarks_root)
    result_filename = get_result_filename(image_path)
    result_path = benchmark_dir / result_filename
    
    if result_path.exists():
        with open(result_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    return {}


import json
import shutil
from pathlib import Path
from typing import Any


def save_individual_result(
    result: dict[str, Any],
    benchmarks_root: Path = Path("benchmarks")
) -> Path:
    """
    Save an individual result by adding/updating it in the image's JSON file.
    Multiple models can save to the same file - their results are stacked by model_id.
    Also saves a copy of the original input image alongside the JSON file.
    """
    image_path = Path(result["image"])
    model_id = result["model_id"]

    benchmark_dir = get_benchmark_path(image_path, benchmarks_root)
    benchmark_dir.mkdir(parents=True, exist_ok=True)

    result_filename = get_result_filename(image_path)
    result_path = benchmark_dir / result_filename

    existing_data = load_existing_results(image_path, benchmarks_root)

    diff_data = result.get("diff", {})
    model_result = {
        "gt": result.get("ground_truth", ""),
        "response": result.get("content", ""),
        "wer": result.get("wer", 0.0),
        "cer": result.get("cer", 0.0),
        "accuracy": diff_data.get("accuracy", 0.0),
        "time": result.get("time_sec", 0.0),
        "diffs": diff_data.get("diffs", []),
        "matches": diff_data.get("matches", 0),
        "deletions": diff_data.get("deletions", 0),
        "insertions": diff_data.get("insertions", 0),
    }

    existing_data[model_id] = model_result

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    image_dest = benchmark_dir / image_path.name
    if not image_dest.exists():
        shutil.copy2(image_path, image_dest)

    return result_path


def is_image_processed_by_any_model(image_path: Path, benchmarks_root: Path = Path("benchmarks")) -> bool:
    """
    Check if an image has been processed by any model.
    
    Args:
        image_path: Path to the image
        benchmarks_root: Root directory for all benchmarks
        
    Returns:
        True if the image has been processed by any model, False otherwise
    """
    existing_data = load_existing_results(image_path, benchmarks_root)
    return len(existing_data) > 0


def update_folder_summary(benchmark_dir: Path) -> Path:
    """
    Update the folder-level summary file based on all individual JSON results in the folder.
    
    The summary contains per-model aggregated statistics:
    - source: the folder path
    - images: number of images processed by this model
    - avg_wer: average word error rate (as percentage)
    - avg_cer: average character error rate (as percentage)
    - avg_accuracy: average accuracy (as percentage)
    - avg_time: average processing time in seconds
    
    Args:
        benchmark_dir: Path to the benchmark folder containing individual result JSONs
        
    Returns:
        Path to the saved summary file
    """
    summary_filename = "_summary.json"
    summary_path = benchmark_dir / summary_filename
    
    model_stats: dict[str, dict[str, float]] = {}
    
    for json_file in benchmark_dir.glob("*.json"):
        if json_file.name == "_summary.json":
            continue
            
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            for model_id, result in data.items():
                if not isinstance(result, dict):
                    continue
                    
                if model_id not in model_stats:
                    model_stats[model_id] = {
                        "wer_sum": 0.0,
                        "cer_sum": 0.0,
                        "accuracy_sum": 0.0,
                        "time_sum": 0.0,
                        "count": 0,
                    }
                
                if "wer" in result and result["wer"] is not None:
                    model_stats[model_id]["wer_sum"] += result["wer"]
                if "cer" in result and result["cer"] is not None:
                    model_stats[model_id]["cer_sum"] += result["cer"]
                if "accuracy" in result and result["accuracy"] is not None:
                    model_stats[model_id]["accuracy_sum"] += result["accuracy"]
                if "time" in result and result["time"] is not None:
                    model_stats[model_id]["time_sum"] += result["time"]
                model_stats[model_id]["count"] += 1
    
    summary: dict[str, Any] = {}
    source_path = str(benchmark_dir).replace("benchmarks/", "")
    
    for model_id, stats in model_stats.items():
        count = stats["count"]
        if count > 0:
            summary[model_id] = {
                "source": source_path,
                "images": count,
                "avg_wer": round(stats["wer_sum"] / count * 100, 15),
                "avg_cer": round(stats["cer_sum"] / count * 100, 15),
                "avg_accuracy": round(stats["accuracy_sum"] / count * 100, 15),
                "avg_time": round(stats["time_sum"] / count, 15),
            }
    
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    return summary_path


def should_skip_image(image_path: Path, model_id: str, benchmarks_root: Path = Path("benchmarks")) -> bool:
    """
    Check if an image should be skipped because it was already processed by this model.
    
    Args:
        image_path: Path to the image
        model_id: The model ID to check
        benchmarks_root: Root directory for all benchmarks
        
    Returns:
        True if the image was already processed by this model, False otherwise
    """
    existing_data = load_existing_results(image_path, benchmarks_root)
    return model_id in existing_data


def generate_manifest(benchmarks_root: Path = Path("benchmarks")) -> Path:
    """
    Generate a manifest.json file containing the overall structure of benchmarked data.
    
    The manifest contains:
    - description: Auto-generated description
    - generated: ISO timestamp of when the manifest was created
    - structure: Hierarchical structure of all benchmark folders with their summaries
      and individual result files
    
    Args:
        benchmarks_root: Root directory for all benchmarks
        
    Returns:
        Path to the saved manifest file
    """
    manifest_path = benchmarks_root / "manifest.json"
    
    structure: dict[str, Any] = {}
    
    for summary_file in benchmarks_root.rglob("_summary.json"):
        rel_path = summary_file.relative_to(benchmarks_root)
        
        parts = list(rel_path.parent.parts)
        
        if len(parts) < 2:
            continue
        
        corpus_index = -1
        for i, part in enumerate(parts):
            if part == "corpus":
                corpus_index = i
                break
        
        start_index = corpus_index + 1 if corpus_index >= 0 else 0
        relevant_parts = parts[start_index:]
        
        if len(relevant_parts) < 2:
            continue
            
        current = structure
        for i, part in enumerate(relevant_parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        doc_folder = relevant_parts[-1]
        
        benchmark_dir = summary_file.parent
        
        individual_files = []
        for json_file in sorted(benchmark_dir.glob("*.json")):
            if json_file.name == "_summary.json":
                continue
            rel_json_path = json_file.relative_to(benchmarks_root)
            individual_files.append(str(rel_json_path))
        
        current[doc_folder] = {
            "aggregated": str(rel_path),
            "individual_files": individual_files,
            "image_count": len(individual_files),
        }
    
    manifest = {
        "description": "Auto-generated manifest of all available JSON files based on the available corpus structure",
        "generated": datetime.now().isoformat(),
        "structure": structure,
    }
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    return manifest_path
