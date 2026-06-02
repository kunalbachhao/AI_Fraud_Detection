from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fraud_model")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()


def predict_email(text: str):
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)

    # This model: 0 = ham (safe), 1 = spam (phishing)
    safe_prob = probabilities[0][0].item()
    phishing_prob = probabilities[0][1].item()

    predicted_class = torch.argmax(probabilities).item()
    label = "Phishing" if predicted_class == 1 else "Safe"

    return {
        "prediction": label,
        "confidence": round(max(phishing_prob, safe_prob) * 100, 2),
        "safe_probability": round(safe_prob * 100, 2),
        "phishing_probability": round(phishing_prob * 100, 2)
    }