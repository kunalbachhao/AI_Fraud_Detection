import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "spam_model.joblib"
DATA_DIR = BASE_DIR / "data"
DATA_PATH = DATA_DIR / "SMSSpamCollection"
DATA_URL = "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"

def download_dataset():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_PATH.exists():
        return
    print("Downloading UCI SMS Spam Collection...")
    with urlopen(DATA_URL, timeout=60) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
        archive.extractall(DATA_DIR)
    print(f"Dataset saved to: {DATA_PATH}")

def load_dataset():
    download_dataset()
    df = pd.read_csv(DATA_PATH, sep="\t", header=None, names=["label", "text"], encoding="utf-8")
    df["label"] = df["label"].map({"ham": 0, "spam": 1})
    return df.dropna().drop_duplicates()

def train():
    df = load_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.20, random_state=42, stratify=df["label"]
    )

    vectorizer = TfidfVectorizer(
        lowercase=True, strip_accents="unicode", ngram_range=(1, 2),
        min_df=2, max_features=100000, sublinear_tf=True
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42)
    model.fit(X_train_vec, y_train)
    predictions = model.predict(X_test_vec)

    print("\n=== Spam Email Checker Evaluation ===")
    print(f"Accuracy : {accuracy_score(y_test, predictions):.4f}")
    print(f"Precision: {precision_score(y_test, predictions):.4f}")
    print(f"Recall   : {recall_score(y_test, predictions):.4f}")
    print(f"F1 score : {f1_score(y_test, predictions):.4f}")
    print(classification_report(y_test, predictions, target_names=["ham", "spam"]))

    joblib.dump(
        {"model": model, "vectorizer": vectorizer, "labels": {"0": "NOT SPAM", "1": "SPAM"}, "dataset": "UCI SMS Spam Collection"},
        MODEL_PATH,
    )
    print(f"Model saved to: {MODEL_PATH}")

if __name__ == "__main__":
    train()
