# api_churn.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import pandas as pd
import numpy as np
from math import exp

# -----------------------------
# Chargement des artefacts
# -----------------------------
try:
    with open("model_churn.pkl", "rb") as f:
        model = pickle.load(f)
    with open("scaler.pkl", "rb") as f:
        scaler = pickle.load(f)
    with open("encoders.pkl", "rb") as f:
        encoders = pickle.load(f)
except Exception as e:
    raise RuntimeError(f"Erreur de chargement des artefacts: {e}")

# -----------------------------
# FastAPI app + CORS
# -----------------------------
app = FastAPI(title="Churn API", version="0.2.0")

# autoriser l’app Streamlit locale et les outils
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost", "http://127.0.0.1", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Schéma d’entrée
# -----------------------------
class CustomerData(BaseModel):
    state: str
    account_length: int
    area_code: int
    international_plan: str
    voice_mail_plan: str
    number_vmail_messages: int
    total_day_minutes: float
    total_day_calls: int
    total_day_charge: float
    total_eve_minutes: float
    total_eve_calls: int
    total_eve_charge: float
    total_night_minutes: float
    total_night_calls: int
    total_night_charge: float
    total_intl_minutes: float
    total_intl_calls: int
    total_intl_charge: float
    customer_service_calls: int

# -----------------------------
# Constantes importantes
# -----------------------------
# Ordre EXACT des features attendu par scaler/model
ORDER = [
    "state","account_length","area_code","international_plan","voice_mail_plan",
    "number_vmail_messages","total_day_minutes","total_day_calls","total_day_charge",
    "total_eve_minutes","total_eve_calls","total_eve_charge",
    "total_night_minutes","total_night_calls","total_night_charge",
    "total_intl_minutes","total_intl_calls","total_intl_charge",
    "customer_service_calls"
]

# Mapping noms Pydantic -> clés des encoders (adapter si tes encoders ont été fit avec des espaces)
ENCODER_MAP = {
    "state": "state",
    "international_plan": "international plan",
    "voice_mail_plan": "voice mail plan",
}

INT_COLS = [
    "account_length","area_code","number_vmail_messages",
    "total_day_calls","total_eve_calls","total_night_calls",
    "total_intl_calls","customer_service_calls",
    "state","international_plan","voice_mail_plan",
]
FLOAT_COLS = [
    "total_day_minutes","total_day_charge",
    "total_eve_minutes","total_eve_charge",
    "total_night_minutes","total_night_charge",
    "total_intl_minutes","total_intl_charge",
]

# -----------------------------
# Helpers
# -----------------------------
def _to_python_list(a):
    """Convertit une liste/classes numpy en types Python pour JSON."""
    out = []
    for x in list(a):
        if isinstance(x, (np.integer,)):
            out.append(int(x))
        elif isinstance(x, (np.floating,)):
            out.append(float(x))
        else:
            out.append(str(x))
    return out

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + exp(-x))

def _predict_proba_binary(model, X) -> float:
    """
    Retourne p(churn) de manière robuste :
    - si predict_proba dispo → proba[:, 1]
    - sinon decision_function → sigmoïde
    - sinon 0.5 (neutre)
    """
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)
        # binaire : [p(no_churn), p(churn)]
        return float(proba[0, 1])

    if hasattr(model, "decision_function"):
        score = model.decision_function(X)
        score = float(score[0]) if hasattr(score, "__len__") else float(score)
        return float(_sigmoid(score))

    return 0.5

# -----------------------------
# Prétraitement
# -----------------------------
def preprocess(data: CustomerData):
    try:
        input_data = data.dict()

        # Encoder variables catégorielles
        for snake_name, enc_key in ENCODER_MAP.items():
            if enc_key not in encoders:
                raise HTTPException(status_code=500, detail=f"Encodeur absent pour '{enc_key}'")
            enc = encoders[enc_key]
            val = input_data[snake_name]

            # cas enc. fit sur STR (idéal)
            if getattr(enc.classes_, "dtype", None) is not None and enc.classes_.dtype.kind in ("U", "S", "O"):
                if val not in enc.classes_:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Valeur inconnue pour '{snake_name}': {val}. "
                               f"Valeurs attendues: {_to_python_list(enc.classes_)}"
                    )
                input_data[snake_name] = int(enc.transform([val])[0])
            else:
                # cas enc. fit sur des entiers (ton cas initial)
                try:
                    code = int(val) if isinstance(val, str) else int(val)
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail=(f"'{snake_name}' doit être un code entier parmi: "
                                f"{_to_python_list(enc.classes_)} "
                                "(tes encoders ont été entraînés sur des codes).")
                    )
                known = set(int(x) for x in enc.classes_)
                if code not in known:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Code inconnu pour '{snake_name}': {code}. Attendu parmi: {sorted(known)}"
                    )
                input_data[snake_name] = code

        # DataFrame dans l'ordre exact
        try:
            df = pd.DataFrame([input_data])[ORDER]
        except KeyError as e:
            missing = [c for c in ORDER if c not in input_data]
            raise HTTPException(status_code=400, detail=f"Colonnes manquantes: {missing}") from e

        # Types
        for c in INT_COLS:
            df[c] = pd.to_numeric(df[c], errors="raise", downcast="integer")
        for c in FLOAT_COLS:
            df[c] = pd.to_numeric(df[c], errors="raise")

        # Scaling
        X = scaler.transform(df)
        return X

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur preprocess: {repr(e)}")

# -----------------------------
# Endpoints
# -----------------------------
@app.get("/")
def read_root():
    return {"message": "API de prédiction du churn opérationnelle 🚀"}

@app.post("/predict")
def predict_churn(
    data: CustomerData,
    threshold: float = Query(0.5, ge=0.0, le=1.0, description="Seuil de décision pour classifier en 'Churn'")
):
    """
    Retourne :
      - prediction (Churn / No Churn) selon le seuil donné
      - prob_churn ∈ [0,1]
      - decision_threshold utilisé
    """
    try:
        X = preprocess(data)
        p_churn = _predict_proba_binary(model, X)
        label = "Churn" if p_churn >= float(threshold) else "No Churn"
        return {
            "prediction": label,
            "prob_churn": round(float(p_churn), 6),
            "decision_threshold": threshold
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur predict: {repr(e)}")

# --- utilitaires pour inspecter les encoders ---
@app.get("/encoders")
def list_encoders():
    return {"encoders": list(encoders.keys())}

@app.get("/encoders/{col}")
def get_encoder_classes(col: str):
    if col not in encoders:
        raise HTTPException(status_code=404, detail=f"Aucun encodeur pour '{col}'")
    classes = encoders[col].classes_
    return {"column": col, "classes": _to_python_list(classes)}
