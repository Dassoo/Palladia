from models.model_utils import to_eval, get_model_display_name
from models.agent import create_agent, create_image_obj
from evaluation.metrics import get_diff, get_metrics
from evaluation.graph import create_graph
from utils.custom_trim import trim_response
from utils.save import to_json, aggregate_folder_results
from utils.update_manifest import update_manifest
from config.loader import load_config

from agno.agent import RunResponse
from agno.utils.pprint import pprint_run_response
from agno.exceptions import ModelProviderError
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pathlib import Path
from rich.console import Console
from rich.text import Text
import asyncio
import time
import random
import yaml
import os

load_dotenv()   
console = Console()

async def run_model(agent, model, executor, image_path: str):
    """Run a model on an image, performing OCR and evaluating the results."""
    image_obj = create_image_obj(model, image_path)
    loop = asyncio.get_event_loop()
    
    start = time.time()
    # Run agent.run in a separate thread to avoid blocking
    response: RunResponse = await loop.run_in_executor(
        executor,
        lambda: agent.run(
            "What text do you see in this image? Please provide an accurate transcription. Return only the transcription, nothing else.",
            images=[image_obj],
            stream=False
        )
    )
    end = time.time()
    exec_time = end - start
    
    gt_path = Path(image_path).with_suffix("").with_suffix(".gt.txt")
    with open(gt_path, "r") as f:
        gt = f.read().rstrip('\n') # Fixed issue with /n impacting accuracy metrics...

    # Fix for silly specific model behaviour
    if model.id == "thudm/glm-4.1v-9b-thinking":
        response = trim_response(response)
    
    # Metrics calculation
    diff, accuracy = get_diff(gt, response.content)
    wer, cer = get_metrics(gt, response.content)
    
    # Print results for each image
    display_name = get_model_display_name(model.id)
    console.print(Text(f"\n(🤖) {display_name}", style="bold blue"))
    pprint_run_response(response)
    console.print(diff)
    console.print(Text(f"WER: {wer:.2%}", style="bold cyan")) # Word error rate (Jiwer)
    console.print(Text(f"CER: {cer:.2%}", style="bold cyan")) # Character error rate (Jiwer)
    console.print(Text(f"Accuracy: {accuracy:.2%}", style="bold blue")) # Accuracy (diff match patch)
    console.print(Text(f"Execution Time: {exec_time:.2f} seconds", style="bold yellow"))
    console.print(Text("_" * 80, style="dim"))
    
    to_json(model, gt, response, wer, cer, accuracy, exec_time, image_path)
    
    return (get_model_display_name(model.id), wer, cer, accuracy, exec_time)
    

async def run_all(image_paths: list[str], source: str):
    """Run all models on a list of images and calculate average metrics."""
    # Create all agents once at startup
    agents = {get_model_display_name(model.id): create_agent(model) for model in to_eval}
    
    # Initialize metrics tracking
    metrics = {
        get_model_display_name(model.id): {
            'wer': [],
            'cer': [],
            'accuracy': [],
            'exec_time': [],
            'total_images': 0
        } for model in to_eval
    }
    
    # Run models on each image
    for image_path in image_paths:
        console.print(Text(f"\nProcessing image: {image_path}", style="dim"))
        executor = ThreadPoolExecutor()
        tasks = [run_model(agents[get_model_display_name(model.id)], model, executor, image_path) for model in to_eval]
        for task in asyncio.as_completed(tasks):
            model_id, wer, cer, accuracy, exec_time = await task
            # Update metrics
            metrics[model_id]['wer'].append(wer)
            metrics[model_id]['cer'].append(cer)
            metrics[model_id]['accuracy'].append(accuracy)
            metrics[model_id]['exec_time'].append(exec_time)
            metrics[model_id]['total_images'] += 1
        executor.shutdown(wait=True)
    
    # Calculate and display average metrics
    console.print(Text("\n" + "="*80, style="bold blue"))
    console.print(Text("AVERAGE METRICS PER MODEL", style="bold blue"))
    console.print(Text("="*80, style="bold blue"))
    
    # Print average metrics for each model
    for model_id, model_metrics in metrics.items():
        if model_metrics['total_images'] > 0:
            avg_wer = sum(model_metrics['wer']) / len(model_metrics['wer'])
            avg_cer = sum(model_metrics['cer']) / len(model_metrics['cer'])
            avg_accuracy = sum(model_metrics['accuracy']) / len(model_metrics['accuracy'])
            avg_exec_time = sum(model_metrics['exec_time']) / len(model_metrics['exec_time'])
            tot_images = model_metrics['total_images']
            
            console.print(Text(f"\n(🤖) {model_id}", style="bold blue"))
            console.print(Text(f"Source: {source}", style="dim"))
            console.print(Text(f"Images processed: {tot_images}", style="dim"))
            console.print(Text(f"Average WER: {avg_wer:.2%}", style="bold cyan"))
            console.print(Text(f"Average CER: {avg_cer:.2%}", style="bold cyan"))
            console.print(Text(f"Average Accuracy: {avg_accuracy:.2%}", style="bold blue"))
            console.print(Text(f"Average Execution Time: {avg_exec_time:.2f} seconds", style="bold yellow"))
            console.print(Text("_"*80, style="dim"))


def select_images_with_priority(source: str, all_images: list[str], images_to_process: int, prioritize_scanned: bool) -> list[str]:
    """Select images with optional prioritization for already scanned images."""
    if not prioritize_scanned:
        # Random selection
        return random.sample(all_images, images_to_process)
    
    # Find images that have already been scanned (with existing JSON results)
    output_folder = Path("docs/json") / source
    scanned_images = []
    unscanned_images = []
    
    for img in all_images:
        # Extract filename preserving double extension (e.g., "00001.bin" from "00001.bin.png")
        img_path = Path(img)
        if img_path.name.endswith('.png'):
            img_name = img_path.name[:-4]  # Remove '.png' to get "00001.bin" or "00283.nrm"
        else:
            img_name = img_path.stem
        json_file = output_folder / f"{img_name}.json"
        
        if json_file.exists():
            scanned_images.append(img)
        else:
            unscanned_images.append(img)
    
    # Images with priority
    selected_images = []
    
    # Add scanned images up to the requested count
    if scanned_images:
        scanned_to_add = min(len(scanned_images), images_to_process)
        selected_images.extend(random.sample(scanned_images, scanned_to_add))
        console.print(Text(f"Selected {scanned_to_add} previously scanned images", style="dim cyan"))
    
    # If exceeding the requested count, add unscanned images
    remaining_needed = images_to_process - len(selected_images)
    if remaining_needed > 0 and unscanned_images:
        unscanned_to_add = min(len(unscanned_images), remaining_needed)
        selected_images.extend(random.sample(unscanned_images, unscanned_to_add))
        console.print(Text(f"Selected {unscanned_to_add} unscanned images", style="dim cyan"))
    
    return selected_images


def main():
    # Check if we have any models to evaluate
    if not to_eval:
        console.print(Text("❌ No models configured for evaluation. Please check your models configuration.", style="bold red"))
        return
    
    try:
        app_config = load_config(verbose=True)  # Show verbose output when running main process
        input_cfg = app_config.input_config.input[0]
        source = input_cfg.path
        images_to_process = input_cfg.images_to_process
        prioritize_scanned = getattr(input_cfg, 'prioritize_scanned', False)
    except Exception as e:
        console.print(f"❌ Configuration error: {e}", style="bold red")
        return
    
    all_images = [f for f in os.listdir(source) if f.endswith('.png')]
    
    if not all_images:
        console.print(Text(f"❌ No images found in {source}", style="bold red"))
        return
    
    if len(all_images) < images_to_process:
        console.print(Text(f"Warning: Only {len(all_images)} images available, processing all of them", style="yellow"))
        images_to_process = len(all_images)
    
    # Select images with optional prioritization
    selected_images = select_images_with_priority(source, all_images, images_to_process, prioritize_scanned)
    image_paths = [os.path.join(source, img) for img in selected_images]
    output_folder = "docs/json/" + source
    
    if prioritize_scanned:
        console.print(Text(f"\nPrioritization enabled: selecting scanned images first", style="dim cyan"))
    
    console.print(Text(f"\nEvaluating {len(to_eval)} models across {len(image_paths)} images...", style="dim"))
    
    try:
        # Run the whole benchmark process
        asyncio.run(run_all(image_paths, source))
        
        # Creating json report
        aggregate_folder_results(output_folder)
        
        # Creating barcharts
        create_graph(output_folder + ".json")
        
        # Update dashboard manifest
        try:
            console.print(Text("Updating dashboard manifest...", style="dim"))
            update_manifest(source)
        except Exception as e:
            console.print(Text(f"⚠️  Could not update dashboard manifest: {e}", style="yellow"))
        
        console.print(Text("\nBenchmark completed. Results saved to docs/json/\n", style="bold green"))
    except ModelProviderError as e:
        console.print(f"❌ Provider error: {e}", style="bold red")
        return
    except KeyboardInterrupt:
        console.print("\n❌ Benchmark interrupted by user.", style="bold red")
        return
    # except Exception as e:
    #     console.print(f"❌ Unexpected error during benchmark: {e}", style="bold red")
    #     pass

if __name__ == "__main__":
    main()