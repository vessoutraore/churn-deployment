# app_streamlit.py
import json
import time
import pickle
import requests
import numpy as np
import streamlit as st

# -----------------------------
# CONFIG GLOBALE
# -----------------------------
st.set_page_config(
    page_title="Customer Churn Prediction",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded",
)

# -----------------------------
# UTILITAIRES
# -----------------------------
@st.cache_resource(show_spinner=False)
def load_encoders(path: str = "encoders.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)

def to_native_types(d: dict) -> dict:
    """Convertit np.int64 / np.float64 -> int / float pour JSON."""
    out = {}
    for k, v in d.items():
        if isinstance(v, (np.integer,)):
            out[k] = int(v)
        elif isinstance(v, (np.floating,)):
            out[k] = float(v)
        else:
            out[k] = v
    return out

def get_json(url: str, timeout: float = 5):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def post_json(url: str, payload: dict, timeout: float = 10):
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def badge(label: str) -> str:
    color = "#f43f5e" if label.lower() == "churn" else "#10b981"
    return f"""
    <span style="
        background:{color}20;
        color:{color};
        padding:0.35rem 0.6rem;
        border:1px solid {color};
        border-radius:999px;
        font-weight:600;
        font-size:0.95rem;">
        {label}
    </span>
    """

# -----------------------------
# DONNÉES / ENCODERS
# -----------------------------
encoders = load_encoders()
# D'après ton encodage actuel, 'state' contient des classes numériques (0..50)
state_options = list(sorted(map(int, encoders["state"].classes_)))
# Plans (0 = no, 1 = yes) — on garde des str qui matchent l’API (si encoders entraînés sur codes)
yn_options = {"no": "0", "yes": "1"}

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("⚙️ Paramètres")

api_base = st.sidebar.text_input(
    "Base URL de l'API",
    value="http://127.0.0.1:8000",
    help="Modifie si l’API tourne ailleurs.",
)
threshold = st.sidebar.slider(
    "Seuil de décision (Churn si proba ≥ seuil)",
    min_value=0.0, max_value=1.0, value=0.50, step=0.01
)
api_url = f"{api_base.rstrip('/')}/predict?threshold={threshold:.2f}"

# Health check
api_status = "❌"
try:
    health = get_json(f"{api_base.rstrip('/')}/", timeout=2)
    api_status = "✅"
except Exception:
    pass
st.sidebar.markdown(f"**API status:** {api_status}")

with st.sidebar.expander("ℹ️ Aide"):
    st.markdown(
        """
- **State** : code numérique encodé par le LabelEncoder (0..50).
- **International / Voice mail plan** : `yes` ou `no` (envoyé comme `'1'`/`'0'` si encoders num.).
- Les autres champs sont numériques.
- Le **seuil** change la décision affichée, pas la probabilité calculée.
"""
    )

# -----------------------------
# EN-TÊTE
# -----------------------------
st.title("📊 Customer Churn Prediction")
st.caption("Formulaire ergonomique • API FastAPI • Probabilité + décision")

# -----------------------------
# FORMULAIRE
# -----------------------------
with st.form("churn_form", clear_on_submit=False):
    st.subheader("Caractéristiques client")

    colA, colB, colC = st.columns(3)
    with colA:
        state = st.selectbox("State (encodé)", options=state_options, index=min(10, len(state_options)-1))
        international_plan = st.selectbox("International Plan", options=list(yn_options.keys()), index=0)
        voice_mail_plan = st.selectbox("Voice Mail Plan", options=list(yn_options.keys()), index=1)

    with colB:
        account_length = st.number_input("Account Length", min_value=0, step=1, value=120)
        area_code = st.number_input("Area Code", min_value=100, max_value=999, step=1, value=415)
        number_vmail_messages = st.number_input("Number of Voice Mail Messages", min_value=0, step=1, value=25)

    with colC:
        customer_service_calls = st.number_input("Customer Service Calls", min_value=0, step=1, value=1)

    st.divider()
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("**Day**")
        total_day_minutes = st.number_input("Total Day Minutes", min_value=0.0, step=0.01, value=265.10)
        total_day_calls = st.number_input("Total Day Calls", min_value=0, step=1, value=110)
        total_day_charge = st.number_input("Total Day Charge", min_value=0.0, step=0.01, value=45.07)

    with c2:
        st.markdown("**Evening**")
        total_eve_minutes = st.number_input("Total Evening Minutes", min_value=0.0, step=0.01, value=197.40)
        total_eve_calls = st.number_input("Total Evening Calls", min_value=0, step=1, value=99)
        total_eve_charge = st.number_input("Total Evening Charge", min_value=0.0, step=0.01, value=16.78)

    with c3:
        st.markdown("**Night & Intl**")
        total_night_minutes = st.number_input("Total Night Minutes", min_value=0.0, step=0.01, value=244.70)
        total_night_calls = st.number_input("Total Night Calls", min_value=0, step=1, value=91)
        total_night_charge = st.number_input("Total Night Charge", min_value=0.0, step=0.01, value=11.01)
        total_intl_minutes = st.number_input("Total Intl Minutes", min_value=0.0, step=0.01, value=10.00)
        total_intl_calls = st.number_input("Total Intl Calls", min_value=0, step=1, value=3)
        total_intl_charge = st.number_input("Total Intl Charge", min_value=0.0, step=0.01, value=2.70)

    # Bouton
    submitted = st.form_submit_button("Predict", use_container_width=True)

# -----------------------------
# ACTION : PREDICT
# -----------------------------
if submitted:
    # mapping yes/no -> "1"/"0" (str) pour coller à l’API si encoders numériques
    intl_str = yn_options[international_plan]
    vmail_str = yn_options[voice_mail_plan]

    payload = {
        "state": str(state),                     # str (encodé)
        "account_length": int(account_length),
        "area_code": int(area_code),
        "international_plan": intl_str,          # "0"/"1"
        "voice_mail_plan": vmail_str,            # "0"/"1"
        "number_vmail_messages": int(number_vmail_messages),
        "total_day_minutes": float(total_day_minutes),
        "total_day_calls": int(total_day_calls),
        "total_day_charge": float(total_day_charge),
        "total_eve_minutes": float(total_eve_minutes),
        "total_eve_calls": int(total_eve_calls),
        "total_eve_charge": float(total_eve_charge),
        "total_night_minutes": float(total_night_minutes),
        "total_night_calls": int(total_night_calls),
        "total_night_charge": float(total_night_charge),
        "total_intl_minutes": float(total_intl_minutes),
        "total_intl_calls": int(total_intl_calls),
        "total_intl_charge": float(total_intl_charge),
        "customer_service_calls": int(customer_service_calls),
    }
    payload = to_native_types(payload)

    with st.spinner("⏳ Prédiction en cours…"):
        try:
            t0 = time.perf_counter()
            resp = post_json(api_url, payload, timeout=15)
            dt = time.perf_counter() - t0

            # lecture robuste
            pred_label = resp.get("prediction", "N/A")
            prob_churn = resp.get("prob_churn", None)  # float ∈ [0,1], si l’API 0.2.0+
            st.markdown(badge(pred_label), unsafe_allow_html=True)

            if isinstance(prob_churn, (float, int)):
                st.metric("Probabilité de churn", f"{prob_churn*100:.1f}%")
                st.progress(min(max(float(prob_churn), 0.0), 1.0))
            else:
                st.info("L’API ne renvoie pas de probabilité. (OK si modèle sans predict_proba)")

            st.caption(f"latence: {dt*1000:.0f} ms • seuil décision: {threshold:.2f}")

            with st.expander("🔍 Détails de la requête/réponse"):
                st.code(json.dumps(payload, indent=2), language="json")
                st.code(json.dumps(resp, indent=2), language="json")

        except requests.exceptions.ConnectionError:
            st.error("❌ Impossible de joindre l'API. Vérifie qu'elle tourne et l’URL dans la sidebar.")
        except requests.exceptions.Timeout:
            st.error("⏱️ L’API a mis trop de temps à répondre (timeout).")
        except requests.exceptions.HTTPError as e:
            try:
                err = e.response.json()
            except Exception:
                err = {"detail": e.response.text}
            st.error(f"🧨 Erreur HTTP {e.response.status_code}\n\n{json.dumps(err, indent=2)}")
        except Exception as e:
            st.error(f"🧨 Erreur inattendue : {e}")

# -----------------------------
# FOOTER
# -----------------------------
st.write("")
st.caption("Made with ❤️ • Streamlit + FastAPI • Demo churn")
