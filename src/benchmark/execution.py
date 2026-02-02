from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from pydantic import SecretStr
from pathlib import Path

from config.schemas import load_config
from utils.converters import convert_to_b64
from utils.preprocessing import random_selection
from benchmark.prompts import SYSTEM_MESSAGE
from benchmark.metrics import get_diff, get_metrics
from benchmark.results_manager import (
    save_individual_result,
    update_folder_summary,
    get_benchmark_path,
)

import os
import asyncio
import time

from dotenv import load_dotenv
load_dotenv()


cfg = load_config()
images = random_selection(cfg.source, cfg.images_to_process, cfg.avoid_rescan)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is not set")


def get_ground_truth_path(image_path: Path) -> Path:
    """
    Get the corresponding ground truth file path for an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Path to the ground truth text file
    """
    filename = image_path.name
    if filename.endswith('.bin.png'):
        gt_filename = filename.replace('.bin.png', '.gt.txt')
    else:
        gt_filename = filename.rsplit('.', 1)[0] + '.gt.txt'
    return image_path.parent / gt_filename


def load_ground_truth(image_path: Path) -> str:
    """
    Load the ground truth text for an image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Ground truth text content, or empty string if file not found or error occurs
    """
    gt_path = get_ground_truth_path(image_path)
    try:
        with open(gt_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""
    except Exception:
        return ""


async def run_model_on_image(
    model_id: str,
    llm: ChatOpenAI,
    image: Path,
    semaphore: asyncio.Semaphore,
):
    """
    Run a specific model on a single image and calculate performance metrics.
    
    Args:
        model_id: ID of the model being used
        llm: ChatOpenAI instance configured with the model
        image: Path to the image to process
        semaphore: Semaphore to limit concurrency
        
    Returns:
        Dictionary containing model_id, image path, processing time, prediction,
        ground truth, diff result, WER, and CER
    """
    async with semaphore:
        start = time.perf_counter()
        
        image_base64 = convert_to_b64(image)
        ground_truth = load_ground_truth(image)

        content = [
            {"type": "text", "text": SYSTEM_MESSAGE},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            },
        ]

        message = HumanMessage(content)
        response = await llm.ainvoke([message])
        
        elapsed = time.perf_counter() - start
        
        prediction = str(response.content)
        
        diff_result = get_diff(prediction, ground_truth)
        wer, cer = get_metrics(prediction, ground_truth)
        
        return {
            "model_id": model_id,
            "image": str(image),
            "time_sec": elapsed,
            "content": prediction,
            "ground_truth": ground_truth,
            "diff": diff_result,
            "wer": wer,
            "cer": cer,
        }


def build_llms(cfg) -> dict[str, ChatOpenAI]:
    """
    Build a dictionary of ChatOpenAI instances for all configured models.
    
    Args:
        cfg: Configuration object containing model information
        
    Returns:
        Dictionary mapping model IDs to ChatOpenAI instances
    """
    assert OPENROUTER_API_KEY is not None
    
    return {
        model.model_id: ChatOpenAI(
            model=model.model_id,
            api_key=SecretStr(OPENROUTER_API_KEY),
            base_url="https://openrouter.ai/api/v1",
        )
        for model in cfg.models
    }
    

async def run_all(cfg, images, max_concurrency=5):
    """
    Run all configured models on selected images.
    
    Args:
        cfg: Configuration object containing model and source information
        images: List of image paths to process
        max_concurrency: Maximum number of concurrent model runs
        
    Returns:
        None
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    llms = build_llms(cfg)

    tasks = []
    processed_folders = set()

    for model_id, llm in llms.items():
        for image in images:
            tasks.append(
                run_model_on_image(
                    model_id=model_id,
                    llm=llm,
                    image=image,
                    semaphore=semaphore,
                )
            )

    for coroutine in asyncio.as_completed(tasks):
        result = await coroutine
        if isinstance(result, Exception | BaseException):
            print("Error:", result)
        else:
            # Save individual result as JSON
            result_path = save_individual_result(result)
            print(f"Saved result to: {result_path}")
            
            # Track the folder for summary update
            benchmark_dir = get_benchmark_path(Path(result["image"]))
            processed_folders.add(benchmark_dir)
            
            print(result)
    
    # Update folder summaries for all processed folders
    for folder in processed_folders:
        summary_path = update_folder_summary(folder)
        print(f"Updated folder summary: {summary_path}")
            

asyncio.run(run_all(cfg, images))
