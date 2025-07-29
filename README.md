# <img src="docs/ocracle.png" alt="OCRacle Logo" width="32" height="32"> OCRacle – A Benchmarking Tool for Vision LMs

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/dassoo) 
[![Website](https://img.shields.io/badge/Website-OCRacle%20Dashboard-555879?style=flat&logo=web)](https://dassoo.github.io/OCRacle)

Evaluate and compare SOTA VLM models on historical image documents using the GT4HistOCR dataset.

## Features

- **Multiple Model Support**: Test various SOTA VLM models
- **Comprehensive Metrics**: WER, CER, accuracy, and execution time
- **Interactive Dashboard**: Web interface with detailed results and diff visualization
- **Individual Image Analysis**: Explore ground truth vs model responses for each image
- **Responsive Design**: Works on desktop and mobile devices

## Installation

**Prerequisites**: Python 3.13+

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd ocr_evaluator
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install .
   ```

2. **Configure API keys:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Download dataset:**
   ```bash
   python utils/download_dataset.py
   ```

## Usage

1. **Run evaluations:**
   ```bash
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   python app.py
   ```

2. **View results:**
   Open `docs/index.html` in your browser for the interactive dashboard with:
   - Overall performance statistics
   - Model comparison tables
   - Individual image analysis with ground truth vs model responses
   - Diff visualization and filtering options


## Results

Results are saved in `docs/json/` with:
- Individual JSON files per image with detailed metrics
- Aggregated performance data across datasets
- PNG charts comparing model performance

## Metrics

- **WER**: Word Error Rate
- **CER**: Character Error Rate  
- **Accuracy**: Exact character match percentage
- **Execution Time**: Processing time per image

## Dashboard Features

The web dashboard includes:
- **Details View**: Click "Details →" buttons to explore individual image results
- **Ground Truth Comparison**: See original text vs model responses
- **Diff Visualization**: Color-coded text differences
- **Filtering**: View results by specific models
- **Sorting**: Order by accuracy, WER, CER, or filename

