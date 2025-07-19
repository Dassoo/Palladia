# OCRacle – A Benchmarking Tool for Vision LLMs

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/dassoo)

A tool for evaluating and comparing the performance of various SOTA multimodal and vision LLM models on historical image documents, based on the GT4HistOCR dataset (https://zenodo.org/records/1344132#.XBdmGPZKg_U).

## Features

- **Multiple Model Support**: Evaluate various SOTA multimodal LLM models.
- **Comprehensive Metrics**: Calculate Word Error Rate (WER), Character Error Rate (CER), and overall accuracy.
- **Visual Comparison**: Color-coded diff visualization between OCR output and ground truth, including a resume graph.
- **Performance Tracking**: Measure and compare execution times across different models.
- **Results Export**: Save evaluation results in JSON format for further analysis.

## Installation

### Prerequisites

- Python 3.13+
- pip or uv package manager

### Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd ocr_evaluator
   ```

2. **Create and activate a virtual environment:**

   Using venv:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

   Or using uv (recommended):
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**

   Using pip:
   ```bash
   pip install .
   ```

   Or using uv:
   ```bash
   uv pip install .
   ```

4. **Set up environment variables:**
   
   Copy the example environment file and add your API keys:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=your_openai_key_here
   GOOGLE_API_KEY=your_google_key_here
   ...
   ```

5. **Download the GT4HistOCR dataset:**

   ```bash
   python utils/download_dataset.py
   ```

### Configuration

The tool uses YAML configuration files located in `config/yaml/`. You can customize:

- **Models to evaluate**: Edit model configurations to enable/disable specific models
- **Input datasets**: Configure which dataset folders to process
- **Evaluation parameters**: Set number of images to process, random sampling, etc.

Run the configuration validation to ensure everything is set up correctly:
```bash
python -m pytest tests/test_config_validation.py -v
```

## Usage

### Quick Start

1. **Activate your virtual environment:**
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Run the interactive app:**
   ```bash
   python app.py
   ```
   This opens a GUI where you can configure models and run evaluations.


### Dataset Structure

The tool expects datasets in the GT4HistOCR format:

```
GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/
├── 00001.bin.png  # Image file
├── 00001.gt.txt   # Ground truth text
├── 00002.bin.png
├── 00002.gt.txt
└── ...
```

### Results

Results are saved in the `results/` directory:
- Individual JSON files per image with detailed metrics
- Aggregated JSON files with averaged performance across datasets  
- PNG bar charts comparing model performance
- Console output with real-time color-coded diffs


## Error Handling & Reliability

OCRacle includes robust error handling to ensure reliable evaluations:

- **Automatic Retries**: Up to 3 attempts for each model call with exponential backoff (1s → 2s → 4s delays)
- **Rate Limit Handling**: Automatically waits and retries when hitting API rate limits
- **Transient Error Recovery**: Detects and retries temporary provider issues (overloads, timeouts, server errors)
- **Authentication Error Detection**: Fails fast for permanent issues like invalid API keys

Example retry behavior:
```
ERROR    API connection error from OpenAI API: Request timed out.                                                                 
WARNING  Attempt 1/6 failed: Request timed out.                                                                                   
ERROR    API connection error from OpenAI API: Request timed out.                                                                 
WARNING  Attempt 2/6 failed: Request timed out.
```

## Metrics

- **Word Error Rate (WER)**: The ratio of word-level errors to the total number of words.
- **Character Error Rate (CER)**: The ratio of character-level errors to the total number of characters.
- **Accuracy**: The percentage of characters that match exactly between the OCR output and ground truth.
- **Execution Time**: The time taken by each model to process the images.

## Output

The tool provides:

1. **Console output** with color-coded diffs and metrics for real-time monitoring
2. **Individual JSON files** in the `results/` directory containing detailed evaluation data per image
3. **Aggregated JSON files** with averaged metrics across entire datasets
4. **Visual barcharts** showing comparative performance across models regarding the evaluated metrics


## Acknowledgements

- GT4HistOCR dataset for providing ground truth data
- All model providers for their APIs
