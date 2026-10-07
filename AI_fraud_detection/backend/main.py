import os
from email import policy
from email.parser import BytesParser
from pathlib import Path

import joblib
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parent / "model"
MODEL_PATH = MODEL_DIR / "spam_model.joblib"

app = FastAPI(title="Spam Email Checker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

classifier = None
vectorizer = None

def load_model():
    global classifier, vectorizer
    if not MODEL_PATH.exists():
        classifier = None
        vectorizer = None
        return
    artifact = joblib.load(MODEL_PATH)
    classifier = artifact["model"]
    vectorizer = artifact["vectorizer"]

load_model()

class EmailRequest(BaseModel):
    subject: str = Field(default="", max_length=5000)
    body: str = Field(..., min_length=1, max_length=100000)

def analyze_text(subject: str, body: str):
    if classifier is None or vectorizer is None:
        raise HTTPException(status_code=503, detail="Spam model is not trained yet. Run: python model/train_spam_model.py")

    text = f"subject: {subject}\n{body}".strip()
    features = vectorizer.transform([text])
    probabilities = classifier.predict_proba(features)[0]
    classes = list(classifier.classes_)
    spam_probability = float(probabilities[classes.index(1)])
    ham_probability = float(probabilities[classes.index(0)])
    prediction = "SPAM" if spam_probability >= 0.5 else "NOT SPAM"

    indicators = []
    lowered = text.lower()
    if "http://" in lowered or "https://" in lowered:
        indicators.append("Contains a URL")
    if any(term in lowered for term in ["urgent", "act now", "immediately", "limited time"]):
        indicators.append("Uses urgency language")
    if any(term in lowered for term in ["winner", "prize", "lottery", "congratulations"]):
        indicators.append("Contains prize/reward language")
    if any(term in lowered for term in ["password", "verify your account", "bank account", "credit card"]):
        indicators.append("Requests sensitive information")
    if "unsubscribe" in lowered:
        indicators.append("Contains an unsubscribe link")

    return {
        "prediction": prediction,
        "spam_probability": round(spam_probability * 100, 2),
        "not_spam_probability": round(ham_probability * 100, 2),
        "confidence": round(max(spam_probability, ham_probability) * 100, 2),
        "indicators": indicators,
    }

@app.get("/")
def root():
    return {"status": "ok", "service": "Spam Email Checker", "model_loaded": classifier is not None}

@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": classifier is not None}

@app.post("/predict")
def predict_email(data: EmailRequest):
    return analyze_text(data.subject, data.body)

@app.post("/predict-file")
async def predict_email_file(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if file.filename and file.filename.lower().endswith(".eml"):
        try:
            message = BytesParser(policy=policy.default).parsebytes(content)
            subject = str(message.get("subject", ""))
            body_parts = []
            if message.is_multipart():
                for part in message.walk():
                    if part.get_content_type() == "text/plain":
                        body_parts.append(part.get_content())
            else:
                body_parts.append(message.get_content())
            body = "\n".join(body_parts)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Could not parse .eml file: {exc}")
    else:
        subject = ""
        body = content.decode("utf-8", errors="ignore")

    if not body.strip():
        raise HTTPException(status_code=400, detail="No readable email text was found.")

    result = analyze_text(subject, body)
    result["filename"] = file.filename
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
