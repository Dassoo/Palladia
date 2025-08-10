import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.model_utils import to_eval, get_model_display_name
from models.agent import create_agent, create_image_obj
from evaluation.metrics import get_diff, get_metrics
from evaluation.graph import create_graph
from utils.custom_trim import trim_response
from utils.save import to_json, aggregate_folder_results
from scripts.update_manifest import update_manifest
from config.loader import load_config

from agno.agent import RunResponse
from agno.utils.pprint import pprint_run_response
from agno.exceptions import ModelProviderError
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.progress import Progress, TaskID, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
import asyncio
import time
import random
import yaml
import json
import os

load_dotenv()   
console = Console()

async def run_single_agent_attempt(agent, model, executor, image_path: str, gt: str):
    """Run a single attempt of the agent on an image."""
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
    
    # Fix for silly specific model behaviour
    if model.id == "thudm/glm-4.1v-9b-thinking":
        response = trim_response(response)
    
    # Metrics calculation
    diff, accuracy = get_diff(gt, response.content)
    wer, cer = get_metrics(gt, response.content)
    
    return response, diff, accuracy, wer, cer, exec_time


async def run_model(agent, model, executor, image_path: str):
    """Run a model on an image, performing OCR and evaluating the results with retry logic."""
    gt_path = Path(image_path).with_suffix("").with_suffix(".gt.txt")
    with open(gt_path, "r") as f:
        gt = f.read().rstrip('\n') # Fixed issue with /n impacting accuracy metrics...
    
    display_name = get_model_display_name(model.id)
    max_attempts = 5
    accuracy_threshold = 0.75
    
    for attempt in range(1, max_attempts + 1):
        try:
            response, diff, accuracy, wer, cer, exec_time = await run_single_agent_attempt(
                agent, model, executor, image_path, gt
            )
            
            # Print results for each attempt
            attempt_text = f" (Attempt {attempt})" if attempt > 1 else ""
            console.print(Text(f"\n(🤖) {display_name}{attempt_text}", style="bold blue"))
            pprint_run_response(response)
            console.print(diff)
            console.print(Text(f"\nWER: {wer:.2%}", style="bold cyan")) # Word error rate (Jiwer)
            console.print(Text(f"CER: {cer:.2%}", style="bold cyan")) # Character error rate (Jiwer)
            console.print(Text(f"Accuracy: {accuracy:.2%}", style="bold blue")) # Accuracy (diff match patch)
            console.print(Text(f"Execution Time: {exec_time:.2f} seconds\n", style="bold cyan"))
            
            # Check if accuracy meets given threshold to ensure benchmark quality
            if accuracy >= accuracy_threshold:
                break
            else:
                if attempt < max_attempts:
                    console.print(Text(f"Accuracy {accuracy:.2%} below threshold {accuracy_threshold:.2%}, retrying...", style="bold yellow"))
                else:
                    console.print(Text("_" * 80, style="dim"))
                    raise Exception(f"\nModel {display_name} failed to achieve {accuracy_threshold:.2%} accuracy after {max_attempts} attempts. Final accuracy: {accuracy:.2%}")
                
        except Exception as e:
            if attempt == max_attempts:
                console.print(Text(f"❌ Final attempt failed: {str(e)}", style="bold red"))
                raise
            else:
                console.print(Text(f"Attempt {attempt} failed: {str(e)}, retrying...", style="bold yellow"))
                continue
    
    console.print(Text("_" * 80, style="dim"))
    to_json(model, gt, response, wer, cer, accuracy, exec_time, image_path)
    
    return (get_model_display_name(model.id), wer, cer, accuracy, exec_time)
    

async def run_all(image_paths: list[str], source: str):
    """Run all models on a list of images and calculate average metrics."""
    # Create all agents once at startup
    agents = {get_model_display_name(model.id): create_agent(model) for model in to_eval}
    
    metrics = {
        get_model_display_name(model.id): {
            'wer': [],
            'cer': [],
            'accuracy': [],
            'exec_time': [],
            'total_images': 0
        } for model in to_eval
    }
    
    # Calculate progress tracking
    total_operations = len(image_paths) * len(to_eval)
    completed_operations = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        refresh_per_second=2
    ) as progress:
        
        # Add main progress task
        main_task = progress.add_task(
            "Running benchmark", 
            total=total_operations
        )
        
        # Run models on each image
        for i, image_path in enumerate(image_paths, 1):
            image_name = Path(image_path).name
            
            executor = ThreadPoolExecutor()
            tasks = [
                run_model(agents[get_model_display_name(model.id)], model, executor, image_path) 
                for model in to_eval
            ]
            
            for task in asyncio.as_completed(tasks):
                model_id, wer, cer, accuracy, exec_time = await task
                
                # Update metrics
                metrics[model_id]['wer'].append(wer)
                metrics[model_id]['cer'].append(cer)
                metrics[model_id]['accuracy'].append(accuracy)
                metrics[model_id]['exec_time'].append(exec_time)
                metrics[model_id]['total_images'] += 1
                
                # Update progress
                completed_operations += 1
                progress.update(
                    main_task, 
                    completed=completed_operations,
                    description=f"\nRunning benchmark - Image {i}/{len(image_paths)}: {image_name}"
                )
            
            executor.shutdown(wait=True)
        
        progress.update(main_task, description="Benchmark completed!")
    
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
    """Select images with optional prioritization for already scanned images missing model evaluations."""
    if not prioritize_scanned:
        # Random selection
        return random.sample(all_images, images_to_process)
    
    # Get all model display names that we're evaluating
    model_names = [get_model_display_name(model.id) for model in to_eval]
    
    # Find images that have JSON files but are missing evaluations for some models
    output_folder = Path("docs/data/json") / source
    priority_images = []
    regular_images = []
    
    for img in all_images:
        # Extract filename preserving double extension (e.g., "00001.bin" from "00001.bin.png")
        img_path = Path(img)
        if img_path.name.endswith('.png'):
            img_name = img_path.name[:-4]  # Remove '.png' extension
        else:
            img_name = img_path.stem
        json_file = output_folder / f"{img_name}.json"
        
        if json_file.exists():
            try:
                # Load existing JSON to check which models are missing
                with open(json_file, 'r') as f:
                    existing_data = json.load(f)
                
                # Check if any of our models are missing from this JSON
                missing_models = [model_name for model_name in model_names if model_name not in existing_data]
                
                if missing_models:
                    # This image has JSON but is missing some model evaluations - prioritize it
                    priority_images.append(img)
                else:
                    # This image has all model evaluations - treat as regular
                    regular_images.append(img)
            except (json.JSONDecodeError, FileNotFoundError):
                # If we can't read the JSON, treat as regular image
                regular_images.append(img)
        else:
            # No JSON file exists - treat as regular image
            regular_images.append(img)
    
    # Select images with priority for missing model evaluations first
    selected_images = []
    
    # Add priority images (those missing model evaluations) first
    if priority_images:
        priority_to_add = min(len(priority_images), images_to_process)
        selected_images.extend(random.sample(priority_images, priority_to_add))
        console.print(Text(f"Selected {priority_to_add} images with missing model evaluations", style="dim cyan"))
    
    # Fill remaining quota with regular images
    remaining_needed = images_to_process - len(selected_images)
    if remaining_needed > 0 and regular_images:
        regular_to_add = min(len(regular_images), remaining_needed)
        selected_images.extend(random.sample(regular_images, regular_to_add))
        console.print(Text(f"Selected {regular_to_add} additional images", style="dim cyan"))
    
    # Summary
    total_with_json = len(priority_images) + len([img for img in regular_images if (output_folder / f"{Path(img).name[:-4] if img.endswith('.png') else Path(img).stem}.json").exists()])
    console.print(Text(f"Priority analysis: {len(priority_images)} images missing evaluations, {total_with_json} total with JSON files", style="dim"))
    
    if len(selected_images) < images_to_process:
        console.print(Text(f"Note: Only {len(selected_images)} images available (requested {images_to_process})", style="dim yellow"))
    
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
    output_folder = "docs/data/json/" + source
    
    if prioritize_scanned:
        console.print(Text(f"\nPrioritization enabled: selecting images missing model evaluations first", style="dim cyan"))
    
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
        
        console.print(Text("\nBenchmark completed. Results saved to docs/data/json/\n", style="bold green"))
    except ModelProviderError as e:
        console.print(f"❌ Provider error: {e}", style="bold red")
        pass
    except KeyboardInterrupt:
        console.print("\n❌ Benchmark interrupted by user.", style="bold red")
        return
    except Exception:
        console.print("\n❌ Benchmark stopped.", style="bold red")
        return
        
if __name__ == "__main__":
    main()