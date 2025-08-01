import json
import os
from pathlib import Path
from PIL import Image
from rich.console import Console
from rich.progress import Progress, TaskID
import argparse

console = Console()

def copy_and_convert_image(source_path: Path, target_path: Path) -> bool:
    """Copy and convert an image to WebP format for web display without compression.
    
    Args:
        source_path: Path to source PNG image
        target_path: Path to target WebP image
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            return True
            
        with Image.open(source_path) as img:
            # Convert to RGB if necessary (for WebP compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            img.save(target_path, "WebP", lossless=True, quality=100)
            
        return True
        
    except Exception as e:
        console.print(f"❌ Error processing {source_path}: {e}", style="red")
        return False

def find_benchmarked_images() -> list[tuple[Path, Path]]:
    """Find all images that have been benchmarked (have corresponding JSON files).
    
    Returns:
        List of tuples: (source_image_path, target_web_path)
    """
    benchmarked_images = []
    docs_json_path = Path("docs/json")
    
    if not docs_json_path.exists():
        console.print("❌ docs/json directory not found", style="red")
        return benchmarked_images
    
    # Walk through all JSON files
    for json_file in docs_json_path.rglob("*.json"):
        # Skip aggregated files (they don't correspond to individual images)
        if json_file.name.endswith(".json") and not json_file.parent.name.endswith(".json"):
            # JSON file structure: docs/json/GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/00021.bin.json
            # Source image: GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/00021.bin.png
            # Target web: docs/images/EarlyModernLatin/1471-Orthographia-Tortellius/00021.webp
            
            relative_path = json_file.relative_to(docs_json_path)
            json_filename = json_file.stem  # e.g., "00021.bin"
            
            # Extract base filename (e.g., "00021" from "00021.bin")
            filename_parts = json_filename.split('.')
            if len(filename_parts) >= 2:
                base_filename = filename_parts[0]
            else:
                base_filename = json_filename
            
            # Construct source image path
            # relative_path is already "GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius"
            source_image_path = relative_path.parent / f"{json_filename}.png"
            
            if source_image_path.exists():
                # Create target web path
                # docs/images/EarlyModernLatin/1471-Orthographia-Tortellius/00021.webp
                web_relative_path = relative_path.parent.relative_to(Path("GT4HistOCR/corpus"))
                target_web_path = Path("docs/images") / web_relative_path / f"{base_filename}.webp"
                
                benchmarked_images.append((source_image_path, target_web_path))
            else:
                console.print(f"Source image not found: {source_image_path}", style="yellow")
    
    return benchmarked_images

def main():
    parser = argparse.ArgumentParser(description="Migrate existing benchmarked images to web format")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without actually doing it")
    parser.add_argument("--force", action="store_true", help="Overwrite existing web images")
    
    args = parser.parse_args()
    
    console.print("Finding benchmarked images...", style="blue")
    benchmarked_images = find_benchmarked_images()
    
    if not benchmarked_images:
        console.print("❌ No benchmarked images found", style="red")
        return
    
    console.print(f"Found {len(benchmarked_images)} benchmarked images", style="green")
    
    if args.dry_run:
        console.print("\nDRY RUN - showing what would be processed:", style="yellow")
        for source_path, target_path in benchmarked_images[:10]:  # Show first 10
            console.print(f"  {source_path} -> {target_path}")
        if len(benchmarked_images) > 10:
            console.print(f"  ... and {len(benchmarked_images) - 10} more")
        return
    
    successful = 0
    skipped = 0
    failed = 0
    
    with Progress() as progress:
        task = progress.add_task("Processing images...", total=len(benchmarked_images))
        
        for source_path, target_path in benchmarked_images:
            # Skip if target exists and not forcing
            if target_path.exists() and not args.force:
                skipped += 1
                progress.advance(task)
                continue
            
            # Copy and convert image
            if copy_and_convert_image(source_path, target_path):
                successful += 1
            else:
                failed += 1
            
            progress.advance(task)
    
    # Summary
    console.print(f"\nMigration completed!", style="bold green")
    console.print(f"  Successfully processed: {successful}")
    console.print(f"  Skipped (already exist): {skipped}")
    console.print(f"  Failed: {failed}")

if __name__ == "__main__":
    main()