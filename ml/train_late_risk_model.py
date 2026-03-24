import json
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


def main():
    features_path = Path("artifacts/features.csv")
    if not features_path.exists():
        raise FileNotFoundError("No existe artifacts/features.csv. Ejecuta ml/build_features.py")

    df = pd.read_csv(features_path)
    x = df[["distance_km", "weight_kg", "hour", "day_of_week"]]
    y = df["late_label"]

    if y.nunique() < 2:
        raise ValueError("Late label no tiene dos clases. Regenera datos con mayor variabilidad.")

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = LogisticRegression(max_iter=500)
    model.fit(x_train, y_train)
    probs = model.predict_proba(x_test)[:, 1]
    auc = roc_auc_score(y_test, probs)

    Path("artifacts").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, "artifacts/late_risk_model.joblib")
    print(f"Modelo Late Risk entrenado. AUC: {auc:.3f}")

    metadata_path = Path("artifacts/model_metadata.json")
    metadata = {
        "model_version": f"eta-risk-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "late_risk_auc": round(float(auc), 4),
    }
    if metadata_path.exists():
        current = json.loads(metadata_path.read_text(encoding="utf-8"))
        current.update(metadata)
        metadata = current
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
