import os
import tarfile
import requests
from tqdm import tqdm

def download_gt4hist():
    """
    Check if GT4HistOCR folder exists, if not, download and extract it.
    The dataset will be downloaded to the project root directory.
    """
    dataset_url = "https://zenodo.org/records/1344132/files/GT4HistOCR.tar?download=1"
    target_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "GT4HistOCR")
    tar_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "GT4HistOCR.tar")
    
    # Check if GT4HistOCR directory already exists
    if os.path.exists(target_dir):
        print("GT4HistOCR dataset is already downloaded.")
        return True
    
    print("Downloading GT4HistOCR dataset...")
    
    try:
        # Stream the download to show progress
        response = requests.get(dataset_url, stream=True)
        response.raise_for_status()
        
        # Get the total file size from headers
        total_size = int(response.headers.get('content-length', 0))
        
        # Download the file with progress bar
        with open(tar_path, 'wb') as f, tqdm(
            desc=tar_path,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                size = f.write(data)
                bar.update(size)
        
        print("Extracting dataset...")
        # Extract and clean upthe tar file
        with tarfile.open(tar_path, 'r') as tar:
            tar.extractall(os.path.dirname(target_dir))
        os.remove(tar_path)
        
        print("GT4HistOCR dataset has been downloaded and extracted successfully!")
        return True
        
    except Exception as e:
        print(f"Error downloading or extracting the dataset: {e}")
        # Clean up partially downloaded file if it exists
        if os.path.exists(tar_path):
            os.remove(tar_path)
        return False

if __name__ == "__main__":
    download_gt4hist()
