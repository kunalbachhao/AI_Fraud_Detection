# Spam Email Checker

A focused spam-email detection application built from the original AI_Fraud_Detection project.

## Architecture

Frontend (HTML/CSS/JavaScript) -> FastAPI -> TF-IDF vectorizer -> Logistic Regression -> SPAM / NOT SPAM

## Features

- Paste an email subject and body
- Upload .txt or .eml files
- Spam and not-spam probabilities
- Model confidence
- Simple content indicators
- Local FastAPI backend
- Reproducible model training

## Setup

From the `AI_fraud_detection` directory:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Train the model:

```bash
python model/train_spam_model.py
```

Start the API:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Then open `frontend/index.html` in a browser, or serve the frontend with a simple static server.

## Dataset

The training script downloads the UCI SMS Spam Collection automatically. It contains messages labeled ham/spam. For a production email system, retrain with a representative email dataset because SMS language differs from full email.

## Important

The classifier is an ML aid, not a security guarantee. Avoid opening links or sharing sensitive information based only on the prediction.
