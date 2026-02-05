# <img src="logo.png" alt="" width="64" height="64"> Palladia

**A Comprehensive Benchmarking Tool for Vision Language Models on Historical Document OCR**

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE.txt)
[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/dassoo)

Palladia is a dedicated benchmarking project designed to evaluate Vision Language Models (VLMs) on historical document OCR tasks using the GT4HistOCR dataset. It provides standardized evaluation metrics that allow researchers and practitioners to compare model performance across various types of historical documents, languages, and preservation conditions. 

A live demo with sample data can be found at https://palladia.vercel.app/.

## Table of Contents

- [What is Palladia?](#what-is-palladia)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Dataset](#dataset)
- [Evaluation Metrics](#evaluation-metrics)
- [Citation](#citation)
- [License](#license)

## What is Palladia?

Historical documents present unique challenges that modern OCR benchmarks often overlook. These include varied typography arising from diverse fonts, handwriting styles, and printing techniques, as well as document degradation caused by aging, stains, or physical damage. 

However, as I further explained on the [website](https://palladia.vercel.app/), the goal of this project is to provide a fair and transparent comparison between models, understanding how quickly both flagship and secondary models are closing the gap in their ability to analyze historical text.

## Key Features

- **Standardized Metrics**: WER, CER, exact match accuracy, and execution time benchmarking
- **Batch Processing**: Efficient evaluation across large document collections
- **Export Capabilities**: Results available in JSON and visualization-ready
- **OpenRouter Friendly**: Any model available on OpenRouter is supported.

## Quick Start

### Prerequisites
- Python 3.13+
- API keys for model providers you want to evaluate
- uv dependency manager

### Installation

```bash
git clone https://github.com/dassoo/Palladia.git
cd Palladia
uv sync
```

### Configuration and usage

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Add your OpenRouter api key to `.env`:
```env
OPENROUTER_API_KEY=your_key_here
```

3. Download the evaluation dataset:
```bash
python src/utils/download_dataset.py
```

4. Edit the `.yaml` files in `src/config` to choose the input data and the models to use

```bash
source: GT4HistOCR/corpus/EarlyModernLatin/1564-Thucydides-Valla
images_to_process: 2
avoid_rescan: True

models:
  - model_id: openai/gpt-5-mini
    enabled: True
    link: https://openrouter.ai/openai/gpt-5-mini
  - model_id: openai/gpt-5
    enabled: False
    link: https://openrouter.ai/openai/gpt-5
```

5. Run your benchmark:

```bash
python src/benchmark/execution.py
```

Results are automatically saved in JSON format in `/benchmarks`, following the same path of the chosen input folder

## Dataset

Palladia relies on the GT4HistOCR dataset, a large-scale collection of historical documents with human-verified transcriptions. It spans multiple centuries, covering the 15th to the 20th, and includes texts in a variety of European languages with historical spelling variations. The dataset encompasses documents in different preservation states and image qualities, providing a realistic benchmark for model evaluation. With over 300,000 lines of transcribed text, GT4HistOCR organizes documents by type, period, and language, delivering high-resolution images alongside their corresponding text files.


## Evaluation Metrics

Palladia provides comprehensive evaluation using industry-standard metrics:

| Metric | Description | Range | Best |
|--------|-------------|-------|------|
| **Word Error Rate (WER)** | Percentage of incorrectly transcribed words | 0-100% | 0% |
| **Character Error Rate (CER)** | Percentage of incorrectly transcribed characters | 0-100% | 0% |
| **Exact Match Accuracy** | Percentage of perfectly transcribed documents | 0-100% | 100% |
| **Execution Time** | Average processing time per document | Seconds | Lower |

It evaluates OCR outputs using standard metrics implemented with Python libraries. Word Error Rate (WER) and Character Error Rate (CER) are computed using the **jiwer** library, while character-level differences and accuracy scoring are handled by **diff_match_patch**. These tools provide a reliable framework for analyzing transcription errors and understanding where models succeed or fail at both word and character levels.


## Citation

If you use Palladia in your research, please cite:

```bibtex
@software{palladia2025,
  title={Palladia: A Benchmarking Tool for Vision Language Models on Historical Document OCR},
  author={Federico Dassiè},
  year={2025},
  url={https://github.com/dassoo/Palladia}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.