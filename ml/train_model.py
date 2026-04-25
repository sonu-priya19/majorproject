# ml/train_model.py
import os
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from ml import feature_extractor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model.pkl")

# ✅ Dummy dataset (replace with real phishing dataset if you have one)
data = [
    ("http://login-paypal.com", 1),
    ("https://secure-update-account.com", 1),
    ("http://google.com", 0),
    ("https://github.com", 0),
    ("http://bank-verify.tk", 1),
    ("https://microsoft.com", 0),
]

df = pd.DataFrame(data, columns=["url", "label"])

# Extract features
X = [feature_extractor.vectorize(feature_extractor.extract_features(u)) for u in df["url"]]
y = df["label"]

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train RandomForest
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

# Save model
joblib.dump(model, "ml/model.pkl")
print("✅ Model trained and saved at ml/model.pkl")

# # ml/train_model.py
# import pandas as pd
# import joblib
# from sklearn.ensemble import RandomForestClassifier
# from sklearn.model_selection import train_test_split
# from sklearn.metrics import classification_report, accuracy_score
# from ml import feature_extractor


# # 1. Load dataset
# # Example: dataset.csv with columns: url,label
# data = pd.read_csv("ml/dataset.csv")

# X = []
# y = []

# for _, row in data.iterrows():
#     feats = feature_extractor.extract_features(row["url"])
#     X.append(feature_extractor.vectorize(feats))
#     y.append(row["label"])

# # 2. Train/test split
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# # 3. Train RandomForestClassifier
# clf = RandomForestClassifier(n_estimators=100, random_state=42)
# clf.fit(X_train, y_train)

# # 4. Evaluate
# y_pred = clf.predict(X_test)
# print("Accuracy:", accuracy_score(y_test, y_pred))
# print("\nClassification Report:\n", classification_report(y_test, y_pred))

# # 5. Save model
# joblib.dump(clf, "ml/model.pkl")
# print("✅ Model trained and saved at ml/model.pkl")
