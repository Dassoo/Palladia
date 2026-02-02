#!/usr/bin/env python3
"""
Script to copy images alongside JSON result files based on matching root names.

Usage:
    python3 scripts/copy_images_for_results.py [--results-dir PATH] [--images-dir PATH] [--extensions EXTENSIONS]

Example:
    python3 scripts/copy_images_for_results.py \
        --results-dir benchmarks/GT4HistOCR \
        --images-dir GT4HistOCR \
        --extensions .png
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import Dict, List, Set


def get_root_name(filename: str) -> str:
    """Extract the root name from a filename (without the last extension)."""
    return Path(filename).stem


def build_image_index(images_dir: Path, extensions: List[str]) -> Dict[str, Path]:
    """
    Build an index mapping root names to image file paths.
    Searches recursively through the images directory.
    """
    image_index: Dict[str, Path] = {}
    for ext in extensions:
        for image_path in images_dir.rglob(f"*{ext}"):
            root_name = get_root_name(image_path.name)
            image_index[root_name] = image_path
    return image_index


def find_json_files(results_dir: Path) -> List[Path]:
    """Get all JSON files from the results directory recursively."""
    return list(results_dir.rglob("*.json"))


def copy_images_for_results(
    results_dir: str,
    images_dir: str,
    extensions: List[str] = [".png", ".jpg", ".jpeg", ".tif", ".tiff"]
) -> tuple[int, int, int]:
    """
    Copy images with matching root names from source to alongside JSON result files.

    Args:
        results_dir: Path to the directory containing JSON result files
        images_dir: Path to the directory containing source images
        extensions: List of image extensions to search for

    Returns:
        Tuple of (copied_count, skipped_count, error_count)
    """
    results_path = Path(results_dir)
    images_path = Path(images_dir)

    if not results_path.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    if not images_path.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    # Build index of available images
    print(f"Building image index from: {images_path}")
    image_index = build_image_index(images_path, extensions)
    print(f"Found {len(image_index)} images")

    # Find all JSON files
    json_files = find_json_files(results_path)
    print(f"Found {len(json_files)} JSON files")

    copied = 0
    skipped = 0
    errors = 0

    for json_file in json_files:
        root_name = get_root_name(json_file.name)

        if root_name in image_index:
            source_image = image_index[root_name]
            dest_path = json_file.parent / source_image.name
            try:
                shutil.copy2(source_image, dest_path)
                print(f"Copied: {source_image.name} -> {json_file.relative_to(results_path)}")
                copied += 1
            except Exception as e:
                print(f"Error copying {source_image} to {dest_path}: {e}")
                errors += 1
        else:
            print(f"Skipped: {json_file.relative_to(results_path)} (no matching image for '{root_name}')")
            skipped += 1

    return copied, skipped, errors


def main():
    parser = argparse.ArgumentParser(
        description="Copy images alongside JSON result files based on matching root names."
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="benchmarks/GT4HistOCR",
        help="Path to directory containing JSON result files (default: benchmarks/GT4HistOCR)"
    )
    parser.add_argument(
        "--images-dir",
        type=str,
        default="GT4HistOCR",
        help="Path to directory containing source images (default: GT4HistOCR)"
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=".png",
        help="Comma-separated list of image extensions to search for (default: .png)"
    )

    args = parser.parse_args()
    extensions = [ext.strip() for ext in args.extensions.split(",")]

    print(f"Results directory: {args.results_dir}")
    print(f"Images directory: {args.images_dir}")
    print(f"Image extensions: {extensions}")
    print("-" * 50)

    try:
        copied, skipped, errors = copy_images_for_results(
            results_dir=args.results_dir,
            images_dir=args.images_dir,
            extensions=extensions
        )
        print("-" * 50)
        print(f"Complete: {copied} copied, {skipped} skipped, {errors} errors")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
