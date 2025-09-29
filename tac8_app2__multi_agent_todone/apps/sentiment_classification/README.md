# Sentiment Classification Application

A Jupyter notebook-based sentiment classification application using both traditional machine learning and transformer-based approaches.

## Setup

This project uses `uv` for dependency management. The virtual environment and dependencies have been configured.

### Prerequisites
- Python 3.12+
- uv package manager

### Installation
```bash
# Dependencies are already configured in pyproject.toml
# To reinstall/update:
uv sync
```

## Project Structure
```
sentiment_classification/
├── .venv/                  # Virtual environment (created by uv)
├── pyproject.toml          # Project configuration and dependencies
├── notebooks/              # Jupyter notebooks
│   └── 01_sentiment_classification_example.ipynb
├── data/                   # Data storage (empty, for future datasets)
├── models/                 # Trained model storage
└── README.md              # This file
```

## Running Notebooks

### Option 1: Using uv run
```bash
# Start Jupyter Lab
uv run jupyter lab

# Or start classic Jupyter Notebook
uv run jupyter notebook
```

### Option 2: Activate venv directly
```bash
# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Then run Jupyter
jupyter lab
```

## Features

The example notebook demonstrates:
- Text preprocessing for sentiment analysis
- Traditional ML approach using TF-IDF and Logistic Regression
- Transformer-based approach using pre-trained DistilBERT
- Data visualization with word clouds
- Model comparison and batch processing
- Custom sentiment analysis functions

## Dependencies

Key packages included:
- **Jupyter ecosystem**: jupyter, ipykernel, jupyterlab
- **Data science**: numpy, pandas, scikit-learn
- **Visualization**: matplotlib, seaborn, wordcloud
- **NLP**: nltk, transformers, torch
- **ML frameworks**: transformers, datasets

## Next Steps

1. Add real-world datasets (IMDB, Twitter, etc.)
2. Fine-tune transformer models
3. Build REST API for model serving
4. Add multi-language support
5. Implement aspect-based sentiment analysis