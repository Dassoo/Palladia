# OCRacle - Multimodal OCR Evaluation Tool

A tool for evaluating and comparing the performance of various SOTA multimodal LLM models on historical image documents, based on the GT4HistOCR dataset (https://zenodo.org/records/1344132#.XBdmGPZKg_U).

## Features

- **Multiple Model Support**: Evaluate various SOTA multimodal LLM models.
- **Comprehensive Metrics**: Calculate Word Error Rate (WER), Character Error Rate (CER), and overall accuracy.
- **Visual Comparison**: Color-coded diff visualization between OCR output and ground truth, including a resume graph.
- **Performance Tracking**: Measure and compare execution times across different models.
- **Results Export**: Save evaluation results in JSON format for further analysis.

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd ocr_evaluator
   ```

2. Install dependencies:

   ```bash
   pip install .
   ```

3. Set up environment variables:
   Create a `.env` file in the project root and add your API keys (see `.env.example`):

   ```
   OPENAI_API_KEY=your_openai_key
   GEMINI_API_KEY=your_gemini_key
   # Add other API keys as needed
   ```

4. Download the GT4HistOCR dataset:

   ```bash
   python utils/download_dataset.py
   ```

## Usage

1. The default benchmark dataset is `GT4HistOCR/corpus/` directory with the following structure:

   ```
   GT4HistOCR/corpus/EarlyModernLatin/1471-Orthographia-Tortellius/
   ├── 00001.bin.png
   ├── 00001.gt.txt
   ├── 00002.bin.png
   ├── 00002.gt.txt
   └── ...
   ```

2. Run the app, from which you can set your models configuration and run the analysis and evaluation.

   ```bash
   python app.py
   ```

3. View the results in the console and in the `results/` directory. A demo of the expected results is already contained into the `demo/` folder, evaluating 3 models on 2 images of a dataset folder.

## Supported Models

- OpenAI
- Google (Gemini)
- Mistral
- Groq (Meta Llama)
- xAI (Grok)
- Anthropic
- OpenRouter (Qwen, Spotlight, InternVL)

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

## Supported Models

- OpenAI
- Google (Gemini)
- Mistral
- Groq (Meta Llama)
- xAI (Grok)
- Anthropic
- OpenRouter (Qwen, Spotlight, InternVL)

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

## Requirements

- Python 3.13+
- Required Python packages (install via `pip install .`):

## Acknowledgements

- GT4HistOCR dataset for providing ground truth data
- All model providers for their APIs
