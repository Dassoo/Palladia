from models.model_utils import to_eval
from models.agent import create_agent, create_image_obj
from evaluation.metrics import get_diff, get_metrics
from utils.save import to_json, to_json_avg

from agno.agent import RunResponse
from agno.utils.pprint import pprint_run_response
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
        gt = f.read()

    diff, accuracy = get_diff(gt, response.content)
    wer, cer = get_metrics(gt, response.content)
    
    # Print results for each image
    console.print(Text(f"\n(🤖) {model.id}", style="bold blue"))
    pprint_run_response(response)
    console.print(diff)
    console.print(Text(f"Time: {exec_time:.2f} seconds", style="bold blue"))
    console.print(Text(f"WER: {wer:.2%}", style="bold cyan")) # Word error rate (Jiwer)
    console.print(Text(f"CER: {cer:.2%}", style="bold cyan")) # Character error rate (Jiwer)
    console.print(Text(f"Accuracy: {accuracy:.2%}", style="bold blue")) # Accuracy (diff match patch)
    console.print(Text("_" * 80, style="dim"))
    
    to_json(model, gt, response, wer, cer, accuracy, exec_time, image_path)
    
    return (model.id, wer, cer, accuracy, exec_time)
    

async def run_all(image_paths: list[str], source: str):
    """Run all models on a list of images and calculate average metrics."""
    # Create all agents once at startup
    agents = {model.id: create_agent(model) for model in to_eval}
    
    # Initialize metrics tracking
    metrics = {
        model.id: {
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
        tasks = [run_model(agents[model.id], model, executor, image_path) for model in to_eval]
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
            
            to_json_avg(model_id, avg_wer, avg_cer, avg_accuracy, avg_exec_time, source, tot_images)
            
            console.print(Text(f"\n(🤖) {model_id}", style="bold blue"))
            console.print(Text(f"Source: {source}", style="dim"))
            console.print(Text(f"Images processed: {tot_images}", style="dim"))
            console.print(Text(f"Average WER: {avg_wer:.2%}", style="bold cyan"))
            console.print(Text(f"Average CER: {avg_cer:.2%}", style="bold cyan"))
            console.print(Text(f"Average Accuracy: {avg_accuracy:.2%}", style="bold blue"))
            console.print(Text(f"Average Execution Time: {avg_exec_time:.2f} seconds", style="bold yellow"))
            console.print(Text("_"*80, style="dim"))


def main():
    # Check if we have any models to evaluate
    if not to_eval:
        console.print(Text("No models configured for evaluation. Please check your models configuration.", style="bold red"))
        return
    
    with open("config/input_config.yaml", 'r') as f:
        config = yaml.safe_load(f)
        source = config['input'][0]['path']
        images_to_process = config['input'][0]['images_to_process']
    
    all_images = [f for f in os.listdir(source) if f.endswith('.png')]
    
    if not all_images:
        console.print(Text(f"No images found in {source}", style="bold red"))
        return
    
    if len(all_images) < images_to_process:
        console.print(Text(f"Warning: Only {len(all_images)} images available, processing all of them", style="yellow"))
        images_to_process = len(all_images)
    
    # Select random non-repeating images
    image_paths = [os.path.join(source, img) for img in random.sample(all_images, images_to_process)]
    
    console.print(Text(f"\nEvaluating {len(to_eval)} models across {len(image_paths)} images...", style="dim"))
    
    # Run the whole process
    asyncio.run(run_all(image_paths, source))
    console.print(Text("\nEvaluation completed. Results saved to results/\n", style="bold green"))


if __name__ == "__main__":
    main()
