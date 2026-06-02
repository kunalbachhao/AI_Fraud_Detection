import pandas as pd
import numpy as np
import re
import joblib
import os
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ==========================================
# 1. CONFIGURATION
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "phishing_site_urls.csv")
MODEL_FILE = os.path.join(BASE_DIR, "xgboost_phishing.pkl")

# ==========================================
# 2. FEATURE EXTRACTION (The Brain)
# ==========================================
def extract_features(url):
    features = [
        len(url),                                   # 1. Length
        url.count('.'),                             # 2. Dots
        url.count('-'),                             # 3. Hyphens
        url.count('@'),                             # 4. @ symbol
        url.count('?'),                             # 5. Question marks
        url.count('='),                             # 6. Equals
        url.count('%'),                             # 7. Percent
        sum(c.isdigit() for c in url),              # 8. Digits
        1 if "https" in url else 0,                 # 9. HTTPS
        1 if "http" in url and "https" not in url else 0, # 10. HTTP
        1 if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url) else 0, # 11. IP Address
        1 if any(word in url.lower() for word in ['login', 'verify', 'update', 'account', 'banking', 'secure']) else 0 # 12. Keywords
    ]
    return features

# ==========================================
# 3. TRAINING LOGIC
# ==========================================
def start_training():
    print(f"--- Looking for data at: {CSV_PATH} ---")
    
    if not os.path.exists(CSV_PATH):
        print("❌ ERROR: csv file not found inside 'model' folder.")
        return

    print("1. Loading Data...")
    df = pd.read_csv(CSV_PATH)

    # Map Labels: bad -> 1, good -> 0
    df['Label'] = df['Label'].map({'bad': 1, 'good': 0})

    print("2. Extracting Features (This takes a moment)...")
    X = np.array([extract_features(url) for url in df['URL']])
    y = df['Label'].values

    print("3. Training XGBoost Model...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, eval_metric='logloss')
    model.fit(X_train, y_train)

    # Evaluate
    acc = accuracy_score(y_test, model.predict(X_test))
    print(f"✅ Model Accuracy: {acc * 100:.2f}%")

    # Save
    joblib.dump(model, MODEL_FILE)
    print(f"💾 Model saved to: {MODEL_FILE}")

if __name__ == "__main__":
    start_training()