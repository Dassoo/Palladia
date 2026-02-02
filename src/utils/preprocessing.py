from benchmark.results_manager import is_image_processed_by_any_model

from pathlib import Path

import random
import os


def is_image_processed(image_path: Path, benchmarks_root: Path = Path("benchmarks")) -> bool:
    """
    Check if an image has already been processed by any model.
    
    Args:
        image_path: Path to the image file
        benchmarks_root: Root directory for all benchmarks
        
    Returns:
        True if the image has been processed by any model, False otherwise
    """
    return is_image_processed_by_any_model(image_path, benchmarks_root)


def random_selection(
    corpora: Path, 
    number_of_images: int, 
    avoid_rescan: bool = False
) -> list[Path]:
    """
    Randomly select images from a corpus.
    
    Args:
        corpora: Path to the directory containing images
        number_of_images: Number of images to select
        avoid_rescan: If True, only select images that haven't been processed yet
        
    Returns:
        List of selected image paths
    """
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif'}
    image_files = []
    
    for file in os.listdir(corpora):
        if os.path.splitext(file.lower())[1] in image_extensions:
            image_path = corpora / file
            
            if avoid_rescan and is_image_processed(image_path):
                continue
                
            image_files.append(image_path)
            
    if len(image_files) == 0:
        return []
    
    actual_count = min(number_of_images, len(image_files))
    
    sample = random.sample(image_files, actual_count)
    
    return sample
