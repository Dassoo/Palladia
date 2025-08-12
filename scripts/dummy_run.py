import asyncio
import random
import time
from pathlib import Path
from rich.console import Console
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from concurrent.futures import ThreadPoolExecutor

console = Console()

# Dummy config and paths
DUMMY_MODELS = [
    {"id": "gpt-4o", "display_name": "GPT-4o"},
    {"id": "claude-4-opus", "display_name": "Claude 4 Opus"},
    {"id": "spotlight", "display_name": "Spotlight"},
    {"id": "qwen-2.5-vl-72b", "display_name": "Qwen 2.5 VL 72B"},
]

DUMMY_IMAGES = [
    "dataset/image_001.png",
    "dataset/image_002.png", 
    "dataset/image_003.png",
    "dataset/image_004.png",
    "dataset/image_005.png",
]

async def dummy_model_run(model: dict, image_path: str, executor: ThreadPoolExecutor):
    """Simulate running a model on an image with random processing time."""
    
    def simulate_processing():
        processing_time = random.uniform(1.0, 5.0)
        time.sleep(processing_time)
        
        wer = random.uniform(0.05, 0.30)
        cer = random.uniform(0.02, 0.15) 
        accuracy = random.uniform(0.70, 0.95)
        
        return wer, cer, accuracy, processing_time
    
    loop = asyncio.get_event_loop()
    wer, cer, accuracy, exec_time = await loop.run_in_executor(executor, simulate_processing)
    
    image_name = Path(image_path).name
    console.print("\n" + "─" * 80)
    console.print(Text(f"🤖 {model['display_name']}", style="bold blue"))
    console.print("─" * 80)
    
    console.print(Text(f"Image: {image_name}", style="dim"))
    console.print(Text(f"Simulated OCR response: 'Lorem ipsum dolor sit amet...'", style="dim"))
    
    console.print("\n" + "─" * 40)
    console.print(Text("Evaluation Result:", style="bold yellow"))
    console.print("─" * 40)
    console.print(Text(f"\nMetrics:", style="dim"))
    console.print(Text(f"  • WER: {wer:.2%}", style="cyan"))
    console.print(Text(f"  • CER: {cer:.2%}", style="cyan"))
    console.print(Text(f"  • Accuracy: {accuracy:.2%}", style="blue"))
    console.print(Text(f"  • Execution Time: {exec_time:.2f} seconds", style="yellow"))
    
    console.print("\n" + "═" * 80 + "\n")
    
    return model['display_name'], wer, cer, accuracy, exec_time

async def run_dummy_benchmark(images: list[str], models: list[dict]):
    """Run dummy benchmark with progress tracking."""
    
    metrics = {
        model['display_name']: {
            'wer': [],
            'cer': [],
            'accuracy': [],
            'exec_time': [],
            'total_images': 0
        } for model in models
    }
    
    # Calculate progress tracking
    total_operations = len(images) * len(models)
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
            "Running dummy benchmark", 
            total=total_operations
        )
        
        # Process each image
        for i, image_path in enumerate(images, 1):
            image_name = Path(image_path).name
            
            executor = ThreadPoolExecutor()
            
            # Create tasks for all models on this image
            tasks = [
                dummy_model_run(model, image_path, executor) 
                for model in models
            ]
            
            # Process completed tasks
            for task in asyncio.as_completed(tasks):
                model_name, wer, cer, accuracy, exec_time = await task
                
                # Update metrics
                metrics[model_name]['wer'].append(wer)
                metrics[model_name]['cer'].append(cer)
                metrics[model_name]['accuracy'].append(accuracy)
                metrics[model_name]['exec_time'].append(exec_time)
                metrics[model_name]['total_images'] += 1
                
                # Update progress
                completed_operations += 1
                progress.update(
                    main_task, 
                    completed=completed_operations,
                    description=f"Image {i}/{len(images)}: {image_name}"
                )
            
            executor.shutdown(wait=True)
        
        progress.update(main_task, description="Dummy benchmark completed!")
    
    # Calculate and display average metrics
    console.print("\n\n" + "═"*80)
    console.print(Text("AVERAGE METRICS PER MODEL", style="bold blue"))
    console.print("═"*80)
    
    # Print average metrics for each model
    for model_name, model_metrics in metrics.items():
        if model_metrics['total_images'] > 0:
            avg_wer = sum(model_metrics['wer']) / len(model_metrics['wer'])
            avg_cer = sum(model_metrics['cer']) / len(model_metrics['cer'])
            avg_accuracy = sum(model_metrics['accuracy']) / len(model_metrics['accuracy'])
            avg_exec_time = sum(model_metrics['exec_time']) / len(model_metrics['exec_time'])
            tot_images = model_metrics['total_images']
            
            console.print(f"\n🤖 {model_name}", style="bold blue")
            console.print(f"├─ Images processed: {tot_images}", style="dim")
            console.print(Text(f"├─ Average WER: {avg_wer:.2%}", style="cyan"))
            console.print(Text(f"├─ Average CER: {avg_cer:.2%}", style="cyan"))
            console.print(Text(f"├─ Average Accuracy: {avg_accuracy:.2%}", style="blue"))
            console.print(Text(f"└─ Average Execution Time: {avg_exec_time:.2f} seconds", style="yellow"))
            console.print("─"*60)

def main():
    """Main function to run the dummy benchmark."""
    console.print(Text("Dummy Benchmark Test", style="bold magenta"))
    console.print(Text("Benchmark simulation without real models or data\n", style="dim"))

    selected_images = DUMMY_IMAGES
    selected_models = DUMMY_MODELS
    
    console.print(Text(f"Selected {len(selected_models)} models and {len(selected_images)} images", style="bold green"))
    console.print(Text("Models: " + ", ".join([m['display_name'] for m in selected_models]), style="green"))
    
    # Run the dummy benchmark
    try:
        asyncio.run(run_dummy_benchmark(selected_images, selected_models))
        console.print(Text("\nDummy benchmark completed successfully!", style="bold green"))
    except KeyboardInterrupt:
        console.print(Text("\n❌ Dummy benchmark interrupted by user", style="bold red"))
    except Exception as e:
        console.print(Text(f"\n❌ Error during dummy benchmark: {e}", style="bold red"))

if __name__ == "__main__":
    main()