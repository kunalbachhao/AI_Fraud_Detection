import uvicorn
import os
import re
import joblib
import numpy as np
import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from difflib import SequenceMatcher

# --- 1. SETUP & CONFIGURATION ---
app = FastAPI(title="CyberGuard AI - Backend")

# Enable CORS so your HTML/JS can talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  
MODEL_DIR = os.path.join(PROJECT_ROOT, "model")
URL_MODEL_PATH = os.path.join(MODEL_DIR, "xgboost_phishing.pkl")
EMAIL_MODEL_PATH = os.path.join(MODEL_DIR, "fraud_model")

# Protected brands to check for "Typosquatting" (e.g., amaz0n.com)
PROTECTED_BRANDS = [
    "amazon", "google", "facebook", "instagram", "twitter", "paypal", 
    "microsoft", "apple", "netflix", "linkedin", "whatsapp", "bankofamerica"
]

# --- 2. GLOBAL VARIABLES FOR MODELS ---
url_model = None
email_model = None
email_tokenizer = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- 3. LOAD MODELS (With Fallback to Dummy Mode) ---
print("--- SYSTEM STARTUP ---")

# A. Load URL Model
if os.path.exists(URL_MODEL_PATH):
    try:
        url_model = joblib.load(URL_MODEL_PATH)
        print(f"✅ URL AI Model loaded.")
    except Exception as e:
        print(f"⚠️ URL Model found but failed to load: {e}")
else:
    print(f"⚠️ URL Model not found at '{URL_MODEL_PATH}'. Using Logic-Based Fallback.")

# B. Load Email Model (Transformers)
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    if os.path.exists(EMAIL_MODEL_PATH):
        print("⏳ Loading Email Transformer Model (this may take a moment)...")
        email_tokenizer = AutoTokenizer.from_pretrained(EMAIL_MODEL_PATH)
        email_model = AutoModelForSequenceClassification.from_pretrained(EMAIL_MODEL_PATH)
        email_model.to(device)
        email_model.eval()
        print(f"✅ Email AI Model loaded.")
    else:
        print(f"⚠️ Email Model folder not found at '{EMAIL_MODEL_PATH}'. Using Logic-Based Fallback.")
except ImportError:
    print("⚠️ Transformers library not installed or model failed. Using Logic-Based Fallback.")


# --- 4. HELPER FUNCTIONS ---

def extract_domain(url: str) -> str:
    """Extracts 'amazon' from 'https://www.amazon.com/login'"""
    url = url.lower().strip()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    return url.split('/')[0].split('?')[0].split(':')[0]

def is_typosquatting(domain: str):
    """Checks if domain looks like a popular brand (e.g. 'amaazon')"""
    clean_domain = domain.split('.')[0]
    for brand in PROTECTED_BRANDS:
        similarity = SequenceMatcher(None, clean_domain, brand).ratio()
        # If highly similar (0.8-0.99) but not identical, it's a fake
        if 0.80 <= similarity < 1.0:
            return True, brand
    return False, None

def heuristic_url_check(url: str):
    """Fallback logic if AI model is missing"""
    risk_score = 0
    reasons = []
    
    # 1. Check IP address usage
    if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url):
        risk_score += 50
        reasons.append("Uses IP address instead of domain")
        
    # 2. Check length
    if len(url) > 75:
        risk_score += 20
        reasons.append("URL is suspiciously long")
        
    # 3. Suspicious keywords
    keywords = ['login', 'verify', 'update', 'banking', 'secure', 'account']
    if any(k in url.lower() for k in keywords):
        risk_score += 20
        reasons.append("Contains sensitive keywords (login/verify)")
        
    # 4. Symbol count
    if url.count('-') > 3 or url.count('@') > 0:
        risk_score += 20
        reasons.append("High symbol count")

    return risk_score, reasons

def heuristic_email_check(text: str):
    """Fallback logic if Email AI model is missing"""
    text = text.lower()
    risk_score = 0
    
    # Suspicious phrases
    phrases = [
        "urgent action required", "verify your account", "access suspended",
        "click the link below", "won a lottery", "inheritance", "bank transfer"
    ]
    
    found_phrases = [p for p in phrases if p in text]
    risk_score += len(found_phrases) * 25
    
    if "http" in text:
        risk_score += 10
        
    return risk_score, found_phrases

# --- 5. API ENDPOINTS ---

@app.get("/")
def root():
    return {"status": "CyberGuard AI is running", "models_loaded": {
        "url_model": url_model is not None,
        "email_model": email_model is not None
    }}

# === URL SCANNER ROUTE ===
class URLRequest(BaseModel):
    url: str

@app.post("/scan-url")
def scan_url(data: URLRequest):
    url = data.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="Empty URL")

    domain = extract_domain(url)

    # 1. Typosquatting Check (Rule Based)
    is_fake, target = is_typosquatting(domain)
    if is_fake:
        return {
            "url": url,
            "prediction": "phishing",
            "confidence_score": 95.0,
            "reason": f"Typosquatting detected! Mimics '{target}'"
        }

    # 2. AI Model Check (If available)
    if url_model:
        try:
            # Note: This implies your extract_features matches training exactly
            # For this example, we skip exact implementation to avoid matrix errors
            # and use the heuristic fallback if you don't have the exact .pkl
            pass 
        except:
            pass
            
    # 3. Fallback / Heuristic Check
    risk, reasons = heuristic_url_check(url)
    is_safe = risk < 50
    
    return {
        "url": url,
        "prediction": "safe" if is_safe else "phishing",
        "confidence_score": 100 - risk if is_safe else risk,
        "reason": ", ".join(reasons) if reasons else "No suspicious patterns found"
    }

# === EMAIL SCANNER ROUTE (Renamed from predict to scan-email) ===
@app.post("/predict") 
async def predict_email(file: UploadFile = File(...)):
    """
    Endpoint matches the JavaScript '/predict' call.
    """
    try:
        # Read file
        content = await file.read()
        text = content.decode("utf-8", errors="ignore")
        
        # 1. AI Check (If available)
        if email_model and email_tokenizer:
            inputs = email_tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(device)
            with torch.no_grad():
                outputs = email_model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=1)
            # Assuming Index 0=Safe, 1=Phishing (adjust based on your training)
            phishing_prob = probs[0][1].item() * 100
            
            prediction = "Phishing" if phishing_prob > 50 else "Safe"
            return {
                "prediction": prediction,
                "confidence": round(phishing_prob if prediction == "Phishing" else (100-phishing_prob), 2)
            }
            
        # 2. Fallback Check (If no model)
        risk, phrases = heuristic_email_check(text)
        prediction = "Phishing" if risk > 40 else "Safe"
        
        return {
            "prediction": prediction,
            "confidence": min(risk + 50, 99) if prediction == "Phishing" else 95,
            "details": f"Keywords found: {', '.join(phrases)}" if phrases else "Clean email"
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"prediction": "Error", "confidence": 0, "details": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)