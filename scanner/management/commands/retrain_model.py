from django.core.management.base import BaseCommand
from django.conf import settings
import os, joblib, csv
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from scanner.models import ScanHistory

MODEL_PATH = os.path.join(settings.BASE_DIR, 'scanner', 'ml', 'model.pkl')
CSV_NAME = os.path.join(settings.BASE_DIR, 'scanner', 'data', 'seed_samples.csv')

# number of fallback features if extractor fails
FALLBACK_FEATURE_LENGTH = 10

class Command(BaseCommand):
    help = "Retrain RandomForest using scanner/data/seed_samples.csv and save scanner/ml/model.pkl"

    def _load_extractor(self):
        """
        Try to import a feature extraction function. Return callable(url)->list or None.
        Looks for several common names/locations used in student projects.
        """
        try:
            from scanner.ml.feature_extraction import extract_features_for_df as ef
            return ef
        except Exception:
            pass
        try:
            from scanner.ml.feature_extraction import extract_features as ef2
            return ef2
        except Exception:
            pass
        try:
            from scanner.ml.feature_extractor import extract_features as ef3
            return ef3
        except Exception:
            pass
        return None

    def handle(self, *args, **options):
        if not os.path.exists(CSV_NAME):
            self.stdout.write(self.style.ERROR("CSV not found: " + CSV_NAME))
            return

        df = pd.read_csv(CSV_NAME)
        # allow several label column names
        label_cols = [c for c in ['label','is_phishing','phish'] if c in df.columns]
        if 'url' not in df.columns or not label_cols:
            self.stdout.write(self.style.ERROR("CSV must contain 'url' and one of label/is_phishing/phish columns"))
            return
        label_col = label_cols[0]
        df = df.dropna(subset=['url'])
        extractor = self._load_extractor()
        X_list = []

        for url in df['url'].tolist():
            if extractor:
                try:
                    fv = extractor(url)
                    # if extractor returns dict -> values
                    if isinstance(fv, dict):
                        row = list(fv.values())
                    else:
                        row = list(fv)
                    # ensure numeric coercion (fallback to zeros)
                    row = [float(x) if _is_number(x) else 0.0 for x in row]
                except Exception as e:
                    # fallback to simple manual features
                    row = _simple_features(url)
            else:
                row = _simple_features(url)
            X_list.append(row)

        # Make X shape uniform: pad shorter rows with zeros
        import numpy as np
        maxlen = max(len(r) for r in X_list) if X_list else FALLBACK_FEATURE_LENGTH
        X = np.array([ (r + [0.0]*(maxlen - len(r))) for r in X_list ], dtype=float)

        # prepare y
        y = df[label_col].apply(lambda v: 1 if str(v).strip().lower() in ('1','true','phishing','yes','phish') else 0).values

        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X, y)

        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(clf, MODEL_PATH)
        self.stdout.write(self.style.SUCCESS("Model retrained and saved to " + MODEL_PATH))

        # Optionally write back to DB (get_or_create prevents duplicates)
        count = 0
        for idx, row in df.iterrows():
            url = row['url']
            result_text = "Phishing" if y[idx] == 1 else "Safe"
            try:
                ScanHistory.objects.get_or_create(
                    url=url,
                    defaults={
                        'result': result_text,
                        'probability': float(95 if y[idx]==1 else 5),  # placeholder
                        'features_json': {},
                        'user': None,
                    }
                )
                count += 1
            except Exception:
                # skip duplicates / errors
                continue
        self.stdout.write(self.style.SUCCESS(f"DB entries updated/ensured: {count}"))

def _is_number(x):
    try:
        float(x)
        return True
    except Exception:
        return False

def _simple_features(url):
    u = str(url).lower()
    s = 0.0
    s += 0.2 if u.startswith('http://') else 0.0
    s += 0.3 if any(k in u for k in ['login','secure','account','verify','update','confirm']) else 0.0
    s += 0.25 if any(c.isdigit() for c in u.split('//')[-1].split('/')[0]) else 0.0
    s += 0.15 if len(u) > 90 else 0.0
    return [len(u), u.count('.'), s, 1.0 if 'https' in u else 0.0] + [0.0]*6
