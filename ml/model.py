# ml/model.py
import pickle, random
import numpy as np
from pathlib import Path
from .feature_extractor import extract_features, vectorize

MODEL_PATH = Path(__file__).resolve().parent / 'model.pkl'
_clf = None

def train_and_save():
    from sklearn.ensemble import RandomForestClassifier
    X, y = [], []
    for _ in range(400):
        feats = {
            'has_https': random.choice([0,1]),
            'length': random.randint(10,150),
            'num_dots': random.randint(1,5),
            'contains_kw': random.choice([0,1]),
            'bad_tld': random.choice([0,1]),
            'num_special': random.randint(0,5),
        }
        X.append(vectorize(feats))
        score = (1-feats['has_https'])*1.5 + feats['contains_kw']*1.2 + feats['bad_tld']*1.1 + (feats['num_special']>=3)
        y.append(1 if score > 1.5 else 0)
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(np.array(X), np.array(y))
    with open(MODEL_PATH, 'wb') as f: pickle.dump(clf, f)
    return clf

def load_model():
    global _clf
    if _clf: return _clf
    if not MODEL_PATH.exists():
        _clf = train_and_save()
    else:
        with open(MODEL_PATH,'rb') as f:
            _clf = pickle.load(f)
    return _clf

def predict_url(clf, url: str):
    feats = extract_features(url)
    vec = np.array([vectorize(feats)])
    proba = clf.predict_proba(vec)[0][1] if hasattr(clf,'predict_proba') else float(clf.predict(vec)[0])
    pred = 1 if proba >= 0.5 else 0
    return pred, float(proba), feats
