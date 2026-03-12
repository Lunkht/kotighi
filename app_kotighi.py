import streamlit as st
import pandas as pd
import numpy as np
import hashlib, time, datetime, requests
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import plotly.express as px
from streamlit_lottie import st_lottie

st.set_page_config(page_title="KOTIGHI AI", layout="wide")

st.markdown("""<style>
/* Style de base supprimé car géré par apply_theme() */
</style>""", unsafe_allow_html=True)

# ── POSTGRESQL INTEGRATION ────────────────────────────────────────
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet

# Configuration de la base de données (à adapter avec tes identifiants)
# Format : postgresql://utilisateur:motdepasse@hote:port/nom_bdd
try:
    DB_URL = st.secrets.get("postgres", {}).get("url", "postgresql://user:pass@localhost:5432/kotighi_db")
except Exception:
    DB_URL = "postgresql://user:pass@localhost:5432/kotighi_db"

def init_db():
    try:
        engine = sa.create_engine(DB_URL)
        # Ici on simulerait la création des tables si elles n'existent pas
        return engine
    except Exception as e:
        st.error(f"Erreur de connexion PostgreSQL : {e}")
        return None

# ── AUTH ──────────────────────────────────────────────────────────
def h(p): return hashlib.sha256(p.encode()).hexdigest()

def check_password_strength(p):
    if len(p) < 8: return False, "Mot de passe trop court (min 8 car.)"
    if not any(c.isupper() for c in p): return False, "Doit contenir une majuscule"
    if not any(c.isdigit() for c in p): return False, "Doit contenir un chiffre"
    return True, "OK"

# Masquage partiel des données sensibles pour l'affichage public/export
def mask_data(data):
    if len(data) > 4:
        return data[:2] + "****" + data[-2:]
    return "****"

# On garde le dictionnaire USERS en fallback si PG n'est pas dispo
USERS = {
    "admin":    {"hash":h("kotighi2024"),"role":"Administrateur","nom":"Admin Principal",   "acces":["Dashboard","Cybersecurite","Sante","Gestion","Assistant"]},
    "analyste": {"hash":h("analyse123"), "role":"Analyste Cyber", "nom":"Jean Dupont",      "acces":["Dashboard","Cybersecurite","Assistant"]},
    "medecin":  {"hash":h("sante456"),   "role":"Medecin",        "nom":"Dr. House",        "acces":["Dashboard","Sante","Assistant"]},
}

def verifier(login, mdp):
    l = login.strip().lower()
    if l in USERS and USERS[l]["hash"] == h(mdp): return USERS[l]
    return None

for k,v in {"connecte":False,"utilisateur":None,"login_nom":None,"tentatives":0,"historique":[],"theme":"Sombre", "chat_history": []}.items():
    if k not in st.session_state: st.session_state[k] = v

# ── THEME CSS ────────────────────────────────────────────────────
def get_logo_html(fill_color):
    try:
        with open("logo.svg", "r") as f:
            svg = f.read()
        svg = svg.replace("<svg", f'<svg fill="{fill_color}" style="width:100%;height:auto;"')
        return svg
    except FileNotFoundError:
        return ""

def apply_theme():
    is_dark = st.session_state.theme == "Sombre"
    # — Premium Color Palette —
    # — Phase 4: Monochromatic Dashboard Palette —
    bg         = "#0B0E14" 
    bg2        = "#07080B" 
    text       = "#E2E8F0" 
    card       = "#11151F" 
    border     = "rgba(255,255,255,0.05)"
    subtext    = "#B4C6EF"
    primary    = "#FFFFFF" # White
    accent     = "#64748B"
    danger     = "#E2E8F0"
    warning    = "#64748B"
    success    = "#FFFFFF"
    sidebar_bg = "#07080B"
    
    # Button & Nav Colors
    btn_bg   = "#FFFFFF"
    btn_text = "#06070A"

    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* ═══ KEYFRAMES ═══ */
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(20px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes slideInLeft {{ from {{ opacity:0; transform:translateX(-30px); }} to {{ opacity:1; transform:translateX(0); }} }}
    @keyframes pulseGlow {{ 0%,100% {{ box-shadow:0 0 15px {primary}30; }} 50% {{ box-shadow:0 0 35px {primary}60; }} }}
    @keyframes shimmer {{ 0% {{ background-position:-200% 0; }} 100% {{ background-position:200% 0; }} }}
    @keyframes blink {{ 50% {{ opacity:.4; }} }}
    @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-10px); }} }}
    @keyframes rotateGlow {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}

    /* ═══ BASE ═══ */
    .stApp {{
        background: {bg} !important;
        color: {text};
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
    .block-container {{ max-width: 1400px !important; padding-top: 2rem; }}

    /* ═══ SCROLLBAR ═══ */
    ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: {border}; border-radius: 10px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: {primary}60; }}

    /* ═══ SIDEBAR ═══ */
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid {border} !important;
    }}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
        animation: slideInLeft .6s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}

    /* ═══ GLASSMORPHISM CORE ═══ */
    .glass-card {{
        background: rgba(17, 21, 31, 0.8) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 24px !important;
        padding: 30px !important;
        box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.45) !important;
        animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
    }}

    /* ═══ APP STRUCTURE ═══ */
    .app-header {{
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 80px;
        background: {bg} !important;
        border-bottom: 1px solid {border};
        z-index: 999990;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 2rem;
        animation: fadeIn 0.5s ease-out;
    }}

    /* Search Bar in Header */
    .search-bar {{
        background: rgba(255,255,255,0.03);
        border: 1px solid {border};
        border-radius: 12px;
        padding: 8px 16px;
        width: 300px;
        color: {subtext};
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }}

    .bottom-nav {{
        display: none !important; /* Managed by Sidebar Drawer in this view */
    }}

    /* Sidebar Navigation Pill Shape */
    .stButton > button {{
        background: transparent !important;
        color: {subtext} !important;
        border: none !important;
        border-radius: 15px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-weight: 500 !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        padding: 12px 20px !important;
        margin-bottom: 4px !important;
        transition: all 0.2s ease;
    }}

    .stButton > button[kind="primary"] {{
        background: {primary} !important;
        color: {bg2} !important;
        box-shadow: 0 4px 15px rgba(255,255,255,0.1) !important;
        font-weight: 700 !important;
    }}

    .stButton > button:hover {{
        background: rgba(255,255,255,0.05) !important;
        color: {primary} !important;
        transform: translateX(5px);
    }}

    /* Sidebar Categories */
    .sidebar-cat {{
        color: {subtext};
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin: 24px 0 12px 12px;
    }}

    /* Adjust main content for fixed header */
    .main-content {{
        margin-top: 80px !important;
        padding: 2rem !important;
        max-width: 1400px;
        margin-left: auto;
        margin-right: auto;
    }}

    /* Hide default Streamlit elements to achieve app look */
    header[data-testid="stHeader"] {{
        background: transparent !important;
        border-bottom: none !important;
    }}
    
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid {border} !important;
    }}

    /* ═══ METRIC CARDS ═══ */
    [data-testid="metric-container"] {{
        background: {card} !important;
        border: 1px solid {border};
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all .35s cubic-bezier(.4,0,.2,1);
        animation: fadeIn .6s ease-out both;
    }}
    [data-testid="metric-container"]:hover {{
        transform: translateY(-6px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: {primary}60;
    }}

    /* ═══ INPUTS ═══ */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {{
        background: rgba(255,255,255,0.03) !important;
        color: {text} !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        padding: 14px 20px !important;
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        transition: all .3s ease;
    }}
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: {primary} !important;
        background: rgba(255,255,255,0.06) !important;
        box-shadow: 0 0 0 4px {primary}20 !important;
    }}
    .stSelectbox > div > div {{
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
    }}

    /* ═══ BUTTONS ═══ */
    .stButton > button {{
        background: {btn_bg} !important;
        color: {btn_text} !important;
        border: 1px solid {btn_bg} !important;
        border-radius: 12px;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.8px;
        padding: 0.8rem 2rem;
        transition: all .4s cubic-bezier(.16, 1, 0.3, 1);
        text-transform: uppercase;
        width: 100%;
    }}
    .stButton > button:hover {{
        background: transparent !important;
        color: {btn_bg} !important;
        transform: scale(1.02);
    }}

    /* ═══ TYPOGRAPHY ═══ */
    h1 {{
        background: linear-gradient(to right, {text}, {primary});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
        font-size: 2.8rem !important;
        letter-spacing: -2px;
        margin-bottom: 0.5rem;
    }}
    h2 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: {text} !important;
        font-size: 1.8rem !important;
        letter-spacing: -1px;
    }}
    h3, h4 {{ font-family: 'Inter', sans-serif !important; font-weight: 600 !important; color: {text} !important; }}

    /* ═══ TABS ═══ */
    .stTabs [data-baseweb="tab-list"] {{
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 6px;
        border: 1px solid rgba(255,255,255,0.1);
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {subtext} !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: .85rem;
        font-weight: 600;
        border-radius: 12px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: {primary} !important;
        color: #000 !important;
        box-shadow: 0 4px 12px {primary}40;
    }}

    /* ═══ CUSTOM COMPONENTS ═══ */
    .k-badge {{
        background: linear-gradient(90deg, {primary}20, {accent}20);
        border: 1px solid {primary}40;
        border-radius: 20px;
        padding: 6px 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: .75rem;
        font-weight: 700;
        color: {primary};
        letter-spacing: 2px;
    }}
    .k-card {{
        background: {card};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 24px;
        transition: all .3s ease;
        animation: fadeIn .5s ease-out;
    }}
    .k-card:hover {{ border-color: {primary}40; box-shadow: 0 8px 30px rgba(0,0,0,.15); }}
    
    .k-card-accent {{
        background: {card};
        border: 1px solid {border};
        border-left: 3px solid {primary};
        border-radius: 12px;
        padding: 20px 24px;
    }}
    .k-alert-danger {{ background: {danger}08; border: 1px solid {danger}25; border-left: 3px solid {danger}; border-radius: 10px; padding: 14px 18px; color: {danger}; font-family: 'JetBrains Mono', monospace; }}
    .k-alert-success {{ background: {success}08; border: 1px solid {success}25; border-left: 3px solid {success}; border-radius: 10px; padding: 14px 18px; color: {success}; font-family: 'JetBrains Mono', monospace; }}
    .k-alert-warning {{ background: {warning}08; border: 1px solid {warning}25; border-left: 3px solid {warning}; border-radius: 10px; padding: 14px 18px; color: {warning}; font-family: 'JetBrains Mono', monospace; }}
    .k-info {{ background: {accent}08; border: 1px solid {accent}20; border-radius: 12px; padding: 16px 20px; color: {accent}; font-family: 'JetBrains Mono', monospace; }}
    .k-mono {{ font-family: 'JetBrains Mono', monospace; }}
    .k-subtext {{ color: {subtext}; font-size: .85rem; }}
    .k-label {{ font-family: 'Inter', sans-serif; font-weight: 600; font-size: .7rem; text-transform: uppercase; letter-spacing: 1.5px; color: {subtext}; margin-bottom: 4px; }}
    
    .soc-panel {{ background: {card}; border: 1px solid {border}; border-radius: 12px; padding: 20px; margin-bottom: 16px; }}
    .soc-header {{ font-family: 'JetBrains Mono', monospace; font-size: .7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; color: {subtext}; border-bottom: 1px solid {border}; padding-bottom: 10px; margin-bottom: 16px; }}
    .status-dot {{ height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }}
    .dot-green {{ background: {success}; box-shadow: 0 0 8px {success}80; }}
    .dot-red {{ background: {danger}; box-shadow: 0 0 8px {danger}80; animation: blink 1.2s ease-in-out infinite; }}
    .dot-yellow {{ background: {warning}; box-shadow: 0 0 8px {warning}60; }}
    
    .clinic-card {{ background: {card}; border: 1px solid {border}; border-left: 3px solid {primary}; border-radius: 14px; padding: 24px; margin-bottom: 16px; transition: all .3s ease; }}
    .clinic-card:hover {{ box-shadow: 0 6px 24px rgba(0,0,0,.15); border-left-color: {accent}; }}
    
    .k-profile {{ background: {card}; border: 1px solid {border}; border-radius: 14px; padding: 16px; margin-bottom: 20px; }}
    .k-profile-name {{ font-weight: 700; color: {text}; font-size: .95rem; margin-bottom: 2px; }}
    .k-profile-role {{ font-family: 'JetBrains Mono', monospace; font-size: .7rem; font-weight: 600; color: {primary}; text-transform: uppercase; letter-spacing: 1px; }}
    
    .feature-card {{ background: {card}; border: 1px solid {border}; border-radius: 14px; padding: 20px; transition: all .3s cubic-bezier(.4,0,.2,1); cursor: pointer; }}
    .feature-card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 28px rgba(0,0,0,.18); border-color: {primary}40; }}

    /* ═══ FORMS GLASSMORPHISM ═══ */
    [data-testid="stForm"] {{
        background: rgba(15, 17, 23, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px !important;
        padding: 2rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2) !important;
    }}

    /* ═══ LOGIN PAGE SPECIFIC ═══ */
    .login-container {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem; min-height: 80vh; }}
    .login-header-text {{ text-align: center; margin-bottom: 2rem; animation: fadeIn 1s ease-out; }}
    
    /* ═══ MAPS & GRAPHS ═══ */
    .graph-container {{
        background: {card} !important;
        border: 1px solid {border};
        border-radius: 20px;
        padding: 15px;
        margin-top: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }}
    
    </style>""", unsafe_allow_html=True)

apply_theme()

# ── ANIMATIONS LOTTIE ─────────────────────────────────────────────
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except: return None

lottie_scan = load_lottieurl("https://lottie.host/6253907c-9b7d-411a-8219-450e82c50257/2j6ZqXy1xS.json") # Radar Scan
lottie_health = load_lottieurl("https://lottie.host/f9202165-424a-4424-8178-0850c410313c/zT1i8r5e1y.json") # Heartbeat
lottie_success = load_lottieurl("https://lottie.host/54003058-0051-4034-a69c-29657685600c/S2g4Q5X06e.json") # Checkmark
lottie_alert = load_lottieurl("https://lottie.host/c528646f-7634-406a-a287-639105437996/gW3s5h8k2f.json") # Warning Triangle

@st.cache_resource
def get_cyber():
    np.random.seed(42); N=4000
    cols = ["requetes_min","duree","octets","ports_scanes","taux_erreur","flag_suspect"]
    n = pd.DataFrame({"requetes_min":np.random.randint(5,300,N//2),"duree":np.random.randint(10,120,N//2),"octets":np.random.randint(500,10000,N//2),"ports_scanes":np.random.randint(1,4,N//2),"taux_erreur":np.random.uniform(0,.1,N//2),"flag_suspect":np.zeros(N//2)})
    a = pd.DataFrame({"requetes_min":np.random.randint(500,8000,N//2),"duree":np.random.randint(0,5,N//2),"octets":np.random.randint(10,300,N//2),"ports_scanes":np.random.randint(20,200,N//2),"taux_erreur":np.random.uniform(.5,1.,N//2),"flag_suspect":np.ones(N//2)})
    df = pd.concat([n.assign(label=0),a.assign(label=1)]).sample(frac=1,random_state=42)
    X,y = df.drop("label",axis=1),df["label"]
    sc = StandardScaler(); Xs = sc.fit_transform(X)
    
    # --- MULTI-MODÈLE : RF + GB ---
    m_rf = RandomForestClassifier(n_estimators=150,random_state=42,n_jobs=-1); m_rf.fit(Xs,y)
    m_gb = GradientBoostingClassifier(n_estimators=100,random_state=42); m_gb.fit(Xs,y)
    
    return m_rf,m_gb,sc

@st.cache_resource
def get_sante():
    np.random.seed(99); N=4000
    # Extension des symptômes pour plus de précision
    cols = ["fievre","toux","fatigue","maux_tete","douleur_gorge","nausees","douleur_thorax","essoufflement","diarrhee","frissons","perte_odorat","douleurs_musculaires","palpitations","vertiges"]
    d = pd.DataFrame({c:np.random.randint(0,2,N) for c in cols})
    
    def diag(r):
        # Règles plus complexes pour l'amélioration de la santé
        if r["fievre"] and r["toux"] and r["perte_odorat"]: return 0 # COVID-19
        if r["fievre"] and r["toux"] and r["fatigue"] and r["douleurs_musculaires"]: return 1 # Grippe
        if r["douleur_thorax"] and r["essoufflement"] and r["palpitations"]: return 2 # Problème cardiaque
        if r["nausees"] and r["diarrhee"] and r["fatigue"]: return 3 # Gastro-entérite
        if r["maux_tete"] and r["fatigue"] and r["vertiges"]: return 4 # Migraine / Fatigue intense
        if r["douleur_gorge"] and r["fievre"] and r["frissons"]: return 5 # Angine
        if r["essoufflement"] and r["douleur_thorax"] and not r["fievre"]: return 6 # Asthme / Stress
        return 7 # Symptômes non spécifiques

    d["label"] = d.apply(diag,axis=1)
    m = RandomForestClassifier(n_estimators=200,random_state=42); m.fit(d.drop("label",axis=1),d["label"])
    
    # --- CONSEILS DE PRÉVENTION ---
    conseils = {
        "COVID-19": ["Isolement immédiat", "Test PCR/Antigénique", "Port du masque", "Surveillance saturation oxygène"],
        "Grippe": ["Repos complet", "Hydratation régulière", "Paracétamol si fièvre", "Éviter contact personnes fragiles"],
        "Problème cardiaque": ["Appeler le 15 (SAMU) immédiatement", "Ne pas conduire", "Rester assis/allongé", "Prendre aspirine si non-allergique (sur avis médical)"],
        "Gastro-entérite": ["Boire solutions réhydratation", "Régime riz/carottes", "Lavage mains fréquent", "Éviter laitages"],
        "Migraine": ["Repos dans le noir/silence", "Caféine peut aider", "Compresse froide sur front", "Éviter écrans"],
        "Angine": ["Consulter pour test TDR", "Boissons chaudes miel/citron", "Gargarisme eau salée", "Surveiller fièvre"],
        "Asthme/Stress": ["Exercices respiration (cohérence cardiaque)", "S'asseoir droit", "Utiliser inhalateur si prescrit", "Éloigner allergènes"],
        "Symptômes non spécifiques": ["Surveiller évolution 24h", "Prendre température matin/soir", "Consulter si aggravation"]
    }
    
    return m,["COVID-19","Grippe","Problème cardiaque","Gastro-entérite","Migraine","Angine","Asthme/Stress","Symptômes non spécifiques"],conseils

def simuler_diagnostic(sympt_checks):
    ms, labels, _ = get_sante() # Get the model and labels
    
    # Map symptom_checks to the feature format expected by the model
    # Ensure all expected features are present, even if not in sympt_checks
    all_symptoms = ["fievre","toux","fatigue","maux_tete","douleur_gorge","nausees","douleur_thorax","essoufflement","diarrhee","frissons","perte_odorat","douleurs_musculaires","palpitations","vertiges"]
    
    feat_data = {s: int(sympt_checks.get(s, False)) for s in all_symptoms}
    feat = pd.DataFrame([feat_data])
    
    pred = ms.predict(feat)[0]
    proba = ms.predict_proba(feat)[0]
    diag = labels[pred]
    conf = proba[pred] * 100
    
    urgence = None
    if "cardiaque" in diag.lower() or "problème cardiaque" in diag.lower():
        urgence = "Risque cardiaque élevé. Consultez un médecin immédiatement."
    elif "covid" in diag.lower():
        urgence = "Possibilité de COVID-19. Isolez-vous et faites un test."
    elif conf < 60:
        urgence = "Faible confiance du diagnostic. Une consultation médicale est recommandée."
    
    return diag, urgence

# ── PAGE LOGIN ────────────────────────────────────────────────────
def page_login():
    if "auth_mode" not in st.session_state: st.session_state.auth_mode = "Connexion"
    
    # Arrière-plan immersif
    st.markdown("""
        <div style='position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; 
                    background: radial-gradient(circle at 20% 30%, #00E5FF15 0%, transparent 50%),
                                radial-gradient(circle at 80% 70%, #8B5CF615 0%, transparent 50%),
                                #06070A;'>
        </div>
    """, unsafe_allow_html=True)

    # Header central
    st.markdown(f"""
        <div style='text-align: center; padding-top: 10vh; margin-bottom: 2rem;'>
            <div style='width: 150px; margin: 0 auto 1rem;'>{get_logo_html('#00E5FF')}</div>
            <p style='color: #64748B; font-weight: 500; letter-spacing: 1.5px; font-size: 0.75rem; text-transform: uppercase;'>Plateforme d'Intelligence Analytique</p>
        </div>
    """, unsafe_allow_html=True)

    # Layout pour le formulaire
    _, col_main, _ = st.columns([1, 1.2, 1])
    
    with col_main:
        # Onglets de navigation
        mode = st.radio("Mode", ["Connexion", "Inscription"], 
                        index=0 if st.session_state.auth_mode == "Connexion" else 1,
                        horizontal=True, label_visibility="collapsed")
        
        if mode != st.session_state.auth_mode:
            st.session_state.auth_mode = mode
            st.rerun()

        st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

        # Formulaire
        if st.session_state.auth_mode == "Connexion":
            if st.session_state.tentatives >= 5:
                st.error("🔒 Sécurité : Trop de tentatives. Compte temporairement bloqué.")
            else:
                with st.form("login_form_new"):
                    login = st.text_input("Identifiant", placeholder="Nom d'utilisateur")
                    password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
                    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                    submitted = st.form_submit_button("S'AUTHENTIFIER")
                
                if submitted:
                    user = verifier(login, password)
                    if user:
                        st.session_state.connecte = True
                        st.session_state.utilisateur = user
                        st.session_state.login_nom = login.lower()
                        st.session_state.tentatives = 0
                        st.toast("✅ Authentification réussie")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.session_state.tentatives += 1
                        st.error("❌ Identifiants invalides")
        
        else:
            with st.form("register_form_new"):
                new_login = st.text_input("Identifiant souhaité", placeholder="Ex: j.dupont")
                new_name  = st.text_input("Nom Complet", placeholder="Jean Dupont")
                new_role  = st.selectbox("Type de Compte", ["Analyste Cyber", "Medecin"])
                new_pass  = st.text_input("Mot de passe", type="password", placeholder="Minimum 8 caractères")
                
                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                reg_submitted = st.form_submit_button("CRÉER MON ESPACE")
                
            if reg_submitted:
                if new_login and new_pass and new_name:
                    is_strong, msg_strong = check_password_strength(new_pass)
                    if not is_strong:
                        st.warning(msg_strong)
                    else:
                        USERS[new_login.lower()] = {
                            "hash": h(new_pass),
                            "role": new_role,
                            "nom": new_name,
                            "acces": ["Dashboard", "Cybersecurite"] if new_role == "Analyste Cyber" else ["Dashboard", "Sante"]
                        }
                        st.success("✨ Compte créé avec succès !")
                        st.session_state.auth_mode = "Connexion"
                        time.sleep(1)
                        st.rerun()
                else:
                    st.error("⚠️ Veuillez remplir tous les champs")

        # Footer
        st.markdown("""
            <div style='margin-top: 2rem; text-align: center;'>
                <span class='k-badge' style='font-size: 0.6rem; opacity: 0.8;'>SÉCURISÉ PAR KOTIGHI SHIELD v3.0</span>
                <p style='color: #64748B; font-family: "JetBrains Mono", monospace; font-size: 0.72rem; margin-top: 1.5rem; line-height: 1.6;'>
                    DEMO : <span style='color: #00E5FF;'>admin</span> / kotighi2024 &nbsp;•&nbsp; 
                    <span style='color: #00E5FF;'>analyste</span> / analyse123 &nbsp;•&nbsp; 
                    <span style='color: #00E5FF;'>medecin</span> / sante456
                </p>
            </div>
        """, unsafe_allow_html=True)


# ── UTILS ANALYTIQUES ─────────────────────────────────────────────
def render_network_map(results):
    if not results: return
    
    # Création du graphe
    nodes_x = []
    nodes_y = []
    node_colors = []
    node_text = []
    
    # Centre du réseau (KOTIGHI)
    nodes_x.append(0)
    nodes_y.append(0)
    node_colors.append("#FFFFFF")
    node_text.append("CENTRE KOTIGHI")
    
    for i, res in enumerate(results):
        angle = 2 * np.pi * i / len(results)
        dist = 1 + (0.5 if res['Status'] != "OK" else 0)
        x = dist * np.cos(angle)
        y = dist * np.sin(angle)
        
        nodes_x.append(x)
        nodes_y.append(y)
        color = "#FFFFFF" if res['Status'] == "CRITIQUE" else ("#B4C6EF" if res['Status'] == "SUSPECT" else "#64748B")
        node_colors.append(color)
        node_text.append(f"IP: {res['IP']}<br>Score: {res['Score']}")
        
    fig = go.Figure()
    
    # Liens
    for i in range(1, len(nodes_x)):
        fig.add_trace(go.Scatter(x=[0, nodes_x[i]], y=[0, nodes_y[i]], 
                                 line=dict(color="rgba(255,255,255,0.05)", width=1), 
                                 hoverinfo='none', mode='lines'))
        
    # Noeuds
    fig.add_trace(go.Scatter(x=nodes_x, y=nodes_y, mode='markers',
                             marker=dict(size=[30] + [20]*(len(nodes_x)-1), color=node_colors, 
                                         line_width=2, line_color="rgba(255,255,255,0.2)"),
                             text=node_text, hoverinfo='text'))
    
    fig.update_layout(
        showlegend=False, 
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=0, b=0, l=0, r=0),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400
    )
    
    st.markdown("<div class='graph-container'>", unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ── APPLICATION PRINCIPALE ────────────────────────────────────────
def app():
    # Application du thème globalement
    apply_theme()
    
    user = st.session_state.utilisateur
    pages = [p for p in user["acces"] if p in ["Dashboard", "Cybersecurite", "Sante", "Gestion", "Assistant"]]
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = pages[0]

    # --- RENDER APP HEADER ---
    st.markdown(f"""
        <div class="app-header">
            <div style="display: flex; align-items: center; gap: 40px;">
                <div style="font-weight: 800; font-size: 1.5rem; letter-spacing: -1px; color: #FFFFFF;">DASHBOARD</div>
                <div class="search-bar">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                    RECHERCHER
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 20px;">
                <div style="text-align: right; line-height: 1.2;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #E2E8F0;">{user['nom']}</div>
                    <div style="font-size: 0.72rem; color: #64748B;">{st.session_state.login_nom}@gmail.com</div>
                </div>
                <div style="width: 44px; height: 44px; background: url('https://api.dicebear.com/7.x/avataaars/svg?seed={user['nom']}') center/cover; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);"></div>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#E2E8F0" stroke-width="2"><path d="m6 9 6 6 6-6"/></svg>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # SIDEBAR
    with st.sidebar:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # CATEGORY: CORE
        st.markdown("<div class='sidebar-cat'>PRINCIPAL</div>", unsafe_allow_html=True)
        nav_items = [
            ("Dashboard", "DASHBOARD"),
            ("Assistant", "ASSISTANT AI")
        ]
        for page_id, label in nav_items:
            if page_id in pages:
                is_active = st.session_state.current_page == page_id
                if st.button(label, key=f"nav_{page_id}", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.current_page = page_id
                    st.rerun()

        # CATEGORY: INTELLIGENCE
        st.markdown("<div class='sidebar-cat'>INTELLIGENCE</div>", unsafe_allow_html=True)
        nav_intel = [
            ("Cybersecurite", "CYBERSÉCURITÉ"),
            ("Sante", "DIAGNOSTIC SANTÉ")
        ]
        for page_id, label in nav_intel:
            if page_id in pages:
                is_active = st.session_state.current_page == page_id
                if st.button(label, key=f"nav_{page_id}", use_container_width=True, type="primary" if is_active else "secondary"):
                    st.session_state.current_page = page_id
                    st.rerun()

        # CATEGORY: SYSTEM
        st.markdown("<div class='sidebar-cat'>SYSTÈME</div>", unsafe_allow_html=True)
        if "Gestion" in pages:
            is_active = st.session_state.current_page == "Gestion"
            if st.button("PARAMÈTRES", key="nav_Gestion", use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.current_page = "Gestion"
                st.rerun()
        
        st.markdown("---")
        theme_choice = st.radio("Thème", ["Sombre", "Clair"], 
                              index=0 if st.session_state.theme == "Sombre" else 1,
                              horizontal=True, label_visibility="collapsed", key="theme_sidebar")
        
        if theme_choice != st.session_state.theme:
            st.session_state.theme = theme_choice
            st.rerun()
            
        if st.button("DÉCONNEXION", use_container_width=True):
            st.session_state.connecte = False
            st.rerun()

    # MAIN CONTENT WRAPPER
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    page = st.session_state.current_page

    # ═══════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ═══════════════════════════════════════════════════════════════
    if page == "Dashboard":
        # --- TOP ROW: KPI CARDS ---
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(f"""
            <div style='background:{card}; border:1px solid {border}; border-radius:16px; padding:20px;'>
                <div style='color:{subtext}; font-size:0.8rem; font-weight:600;'>CONNEXIONS FLUX</div>
                <div style='display:flex; align-items:baseline; gap:8px; margin-top:8px;'>
                    <div style='font-size:1.6rem; font-weight:800; color:#E2E8F0;'>12,847</div>
                </div>
                <div style='color:#E2E8F0; font-size:0.72rem; font-weight:700; margin-top:4px;'>+33.45%</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div style='background:{card}; border:1px solid {border}; border-radius:16px; padding:20px;'>
                <div style='color:{subtext}; font-size:0.8rem; font-weight:600;'>ALERTES BLOQUÉES</div>
                <div style='display:flex; align-items:baseline; gap:8px; margin-top:8px;'>
                    <div style='font-size:1.6rem; font-weight:800; color:#E2E8F0;'>1,203</div>
                </div>
                <div style='color:#E2E8F0; font-size:0.72rem; font-weight:700; margin-top:4px;'>-15.22%</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            st.markdown(f"""
            <div style='background:{card}; border:1px solid {border}; border-radius:16px; padding:20px;'>
                <div style='color:{subtext}; font-size:0.8rem; font-weight:600;'>FIABILITÉ IA</div>
                <div style='display:flex; align-items:baseline; gap:8px; margin-top:8px;'>
                    <div style='font-size:1.6rem; font-weight:800; color:#E2E8F0;'>99.2%</div>
                </div>
                <div style='color:#E2E8F0; font-size:0.72rem; font-weight:700; margin-top:4px;'>+0.12%</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c4:
            st.markdown(f"""
            <div style='background:{card}; border:1px solid {border}; border-radius:16px; padding:20px;'>
                <div style='color:{subtext}; font-size:0.8rem; font-weight:600;'>VITESSE SCAN</div>
                <div style='display:flex; align-items:baseline; gap:8px; margin-top:8px;'>
                    <div style='font-size:1.6rem; font-weight:800; color:#E2E8F0;'>1.2S</div>
                </div>
                <div style='color:#E2E8F0; font-size:0.72rem; font-weight:700; margin-top:4px;'>+6.55%</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        # --- MIDDLE ROW: LARGE CHART & SIDE BLOCKS ---
        col_main, col_side = st.columns([2.2, 1])
        
        with col_main:
            st.markdown(f"""
            <div style='background:{card}; border:1px solid {border}; border-radius:24px; padding:24px; height:450px;'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                    <div>
                        <div style='color:{subtext}; font-size:0.85rem; font-weight:600;'>FLUX D'ACTIVITÉ</div>
                        <div style='font-size:1.8rem; font-weight:800; color:#E2E8F0;'>405,654 <span style='color:#E2E8F0; font-size:0.9rem;'>+43.46%</span></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Line Chart with Monochromatic Scale
            hours = list(range(10))
            data_val = [310, 330, 315, 340, 360, 355, 390, 350, 360, 355]
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hours, y=data_val, 
                mode='lines+markers',
                line=dict(color="#FFFFFF", width=3),
                marker=dict(size=8, color="#0B0E14", line=dict(color="#FFFFFF", width=2)),
                fill='tozeroy',
                fillcolor='rgba(255, 255, 255, 0.05)'
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=300, margin=dict(t=10, b=0, l=0, r=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)", zeroline=False, showticklabels=True, color="#64748B"),
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
            
            # --- BOTTOM LIST Section ---
            st.markdown(f"""
            <div style='background:{card}; border:1px solid {border}; border-radius:24px; padding:24px;'>
                <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;'>
                    <div style='color:{subtext}; font-size:0.9rem; font-weight:700;'>LOGS RÉCENTS</div>
                    <div style='color:{primary}; font-size:0.75rem; font-weight:700; cursor:pointer;'>VOIR TOUT</div>
                </div>
            """, unsafe_allow_html=True)
            
            recent_items = [
                ("KOTIGHI API", "System Check: Live", "10:45", "Live"),
                ("NETWORK SCAN", "Port scanning: Complete", "09:30", "Done"),
                ("HEALTH AI", "Biomarker analysis", "Yesterday", "PDF"),
            ]
            for title, desc, time_str, status in recent_items:
                st.markdown(f"""
                <div style='display:flex; justify-content:space-between; align-items:center; padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.03);'>
                    <div style='display:flex; align-items:center; gap:16px;'>
                        <div style='width:36px; height:36px; background:rgba(255,255,255,0.05); border-radius:10px; display:flex; align-items:center; justify-content:center; color:#FFFFFF; font-size:0.75rem; font-weight:800;'>IA</div>
                        <div>
                            <div style='color:#E2E8F0; font-size:0.9rem; font-weight:700;'>{title}</div>
                            <div style='color:{subtext}; font-size:0.75rem;'>{desc}</div>
                        </div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='color:#E2E8F0; font-size:0.8rem; font-weight:600;'>{time_str}</div>
                        <div style='color:#FFFFFF; font-size:0.72rem; font-weight:700;'>{status}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_side:
            # Satisfaction / Gauge Block
            st.markdown(f"""
            <div style='background:{card}; border:1px solid {border}; border-radius:24px; padding:24px; height:240px; margin-bottom:20px; display:flex; flex-direction:column; align-items:center;'>
                <div style='color:{subtext}; font-size:0.85rem; font-weight:600; width:100%'>Stabilité Système</div>
            """, unsafe_allow_html=True)
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = 75.5,
                domain = {'x': [0, 1], 'y': [0, 1]},
                number = {'font': {'size': 44, 'color': '#E2E8F0', 'family': 'Inter'}},
                gauge = {
                    'axis': {'range': [None, 100], 'visible': False},
                    'bar': {'color': "#FFFFFF", 'thickness': 0.15},
                    'bgcolor': "rgba(255,255,255,0.03)",
                    'borderwidth': 0,
                }
            ))
            fig_gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                height=180, margin=dict(t=0, b=0, l=10, r=10),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Promo / Info Block
            st.markdown(f"""
            <div style='background:linear-gradient(180deg, {card} 0%, rgba(255,255,255,0.02) 100%); border:1px solid {border}; border-radius:24px; padding:24px; height:260px;'>
                 <div style='color:#FFFFFF; font-weight:800; font-size:1.1rem; line-height:1.3; margin-top:10px;'>ÉVOLUEZ VERS<br>KOTIGHI PRO</div>
                 <p style='color:{subtext}; font-size:0.82rem; margin-top:12px; line-height:1.5;'>Obtenez des analyses réseau temps-réel et des rapports médicaux détaillés en un clic.</p>
                 <div style='margin-top:24px; background:#FFFFFF; color:#0B0E14; padding:12px; border-radius:12px; text-align:center; font-weight:800; font-size:0.85rem; cursor:pointer;'>EN SAVOIR PLUS</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
        
        # --- ALERTS SECION ---
        st.markdown("#### ALERTES D'URGENCE")
        alerts = [h for h in st.session_state.historique if h.get("Resultat") in ["CRITIQUE", "URGENT"] or "cardiaque" in str(h.get("Resultat")).lower()]
        
        if alerts:
            for alert in alerts[-2:]: # Show last 2
                st.markdown(f"""
                <div class='k-alert-danger' style='margin-bottom:10px; border-radius:16px; background:rgba(255,255,255,0.05); padding:16px; border:1px solid rgba(255,255,255,0.1);'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <b style='color:#FFFFFF;'>{alert['Module'].upper()} : {alert['Resultat']}</b>
                        <span style='font-size:0.7rem; color:{subtext};'>{alert['Date']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color:{subtext}; font-style:italic;'>Aucune alerte critique.</p>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════════
    
    # ═══════════════════════════════════════════════════════════════
    #  CYBERSECURITE — SOC TERMINAL
    # ═══════════════════════════════════════════════════════════════
    elif page == "Cybersecurite":
        st.markdown("## MODULE CYBER", unsafe_allow_html=True)
        st.divider()
        
        m_rf, m_gb, sc = get_cyber()
        
        # Initialisation Watchlist
        if "watchlist" not in st.session_state: st.session_state.watchlist = []
        
        col_main, col_side = st.columns([3, 1])
        
        with col_main:
            # ONGLETS FONCTIONNELS
            tab1, tab2 = st.tabs(["SCAN", "SURVEILLANCE"])
            
            with tab1:
                st.markdown("### Cibles d'Analyse")
                
                # Gestion dynamique des champs d'IP
                if "ip_count" not in st.session_state: st.session_state.ip_count = 1
                
                # Boutons +/- pour ajouter/retirer des champs
                c_add, c_rem, _ = st.columns([1, 1, 4])
                if c_add.button("AJOUTER CIBLE", key="add_ip"): 
                    st.session_state.ip_count += 1
                    st.rerun()
                if c_rem.button("RETIRER CIBLE", key="rem_ip") and st.session_state.ip_count > 1: 
                    st.session_state.ip_count -= 1
                    st.rerun()
                
                ips_list = []
                cols = st.columns(3) # Grille de 3 colonnes pour les inputs
                for i in range(st.session_state.ip_count):
                    with cols[i % 3]:
                        val = st.text_input(f"IP #{i+1}", key=f"ip_input_{i}", placeholder="192.168.x.x")
                        if val: ips_list.append(val)
                
                st.markdown("---")
                st.caption("Paramètres de Simulation")
                c1, c2, c3 = st.columns(3)
                with c1: req = st.number_input("Req/min", 0, 10000, 150)
                with c2: ports = st.number_input("Ports", 0, 1000, 5)
                with c3: terr = st.number_input("Erreur", 0.0, 1.0, 0.01)
                
                st.markdown("<br>", unsafe_allow_html=True)
                col_act, col_add = st.columns([1, 1])
                with col_act:
                    go_scan = st.button("LANCER SCAN", type="primary", use_container_width=True)
                with col_add:
                    add_watch = st.button("AJOUTER SURVEILLANCE", use_container_width=True)
                
                if go_scan and ips_list:
                    ips = [ip.strip() for ip in ips_list if ip.strip()]
                    results = []
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, ip in enumerate(ips):
                        status_text.text(f"Scanning {ip}...")
                        # Simulation variation données
                        sim_req = req + np.random.randint(-50, 50)
                        sim_ports = ports + np.random.randint(0, 2)
                        
                        feat = pd.DataFrame([{"requetes_min":sim_req,"duree":45,"octets":2500,"ports_scanes":sim_ports,"taux_erreur":terr,"flag_suspect":0}])
                        feat_scaled = sc.transform(feat)
                        
                        # Vote
                        p_rf = m_rf.predict_proba(feat_scaled)[0]
                        p_gb = m_gb.predict_proba(feat_scaled)[0]
                        proba_moy = (p_rf + p_gb) / 2
                        score = proba_moy[1]
                        
                        verdict = "CRITIQUE" if score > 0.8 else ("SUSPECT" if score > 0.5 else "OK")
                        results.append({"IP": ip, "Status": verdict, "Score": f"{score*100:.1f}%", "Ports": sim_ports})
                        
                        time.sleep(0.1) # Effet scan rapide
                        progress_bar.progress((i + 1) / len(ips))
                        
                    status_text.empty()
                    progress_bar.empty()
                    
                    st.markdown("### Résultats")
                    df_res = pd.DataFrame(results)
                    st.dataframe(df_res, use_container_width=True)
                    
                    # LOGGING PERSISTANT
                    for res in results:
                        log_entry = {
                            "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "Module": "Cyber",
                            "Resultat": res["Status"],
                            "Confiance": res["Score"],
                            "Utilisateur": st.session_state.utilisateur["nom"],
                            "Detail": f"IP {res['IP']}, Ports {res['Ports']}"
                        }
                        st.session_state.historique.append(log_entry)
                        
                    # Affichage Carte
                    render_network_map(results)
                
                if add_watch and ips_list:
                    new_ips = [ip.strip() for ip in ips_list if ip.strip()]
                    for ip in new_ips:
                        if ip not in [w["ip"] for w in st.session_state.watchlist]:
                            st.session_state.watchlist.append({"ip": ip, "added_at": datetime.datetime.now().strftime("%H:%M"), "status": "PENDING"})
                    st.success(f"{len(new_ips)} cible(s) ajoutée(s).")

            with tab2:
                st.markdown("### Surveillance Active")
                
                if not st.session_state.watchlist:
                    st.info("Aucune cible surveillée.")
                else:
                    col_metrics = st.columns(3)
                    col_metrics[0].metric("Cibles", len(st.session_state.watchlist))
                    col_metrics[1].metric("Alertes", np.random.randint(0, 5))
                    col_metrics[2].metric("Trafic", f"{np.random.randint(50, 500)} Mbps")
                    
                    st.markdown("---")
                    
                    for target in st.session_state.watchlist:
                        is_threat = np.random.random() > 0.8
                        status_txt = "MENACE" if is_threat else "NORMAL"
                        traffic = np.random.randint(100, 2000)
                        
                        cols = st.columns([2, 1, 1, 1])
                        with cols[0]: st.markdown(f"**{target['ip']}**")
                        with cols[1]: st.caption(f"{traffic} req/m")
                        with cols[2]: st.markdown(f"<span style='color:{'#EF4444' if is_threat else '#10B981'}'>{status_txt}</span>", unsafe_allow_html=True)
                        with cols[3]: 
                            if st.button("X", key=f"del_{target['ip']}"):
                                st.session_state.watchlist.remove(target)
                                st.rerun()
                        st.markdown("<hr style='margin:5px 0'>", unsafe_allow_html=True)
                        
                        if is_threat:
                            st.toast(f"Alerte : {target['ip']}")

        with col_side:
            st.markdown("### Événements")
            events = [
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] SCAN BLOCK 192.168.1.45",
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] SSH FAIL 10.0.0.12",
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] FW UPDATE SUCCESS"
            ]
            for evt in events:
                st.caption(evt)
            
            st.markdown("---")
            st.markdown("### Système")
            st.caption("CPU Usage")
            st.progress(88)
            st.caption("RAM Usage")
            st.progress(45)

    # ═══════════════════════════════════════════════════════════════
    #  SANTE — MODULE CLINIQUE
    # ═══════════════════════════════════════════════════════════════
    elif page == "Sante":
        st.markdown(f"""
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h2 style='margin:0;'>DIAGNOSTIC SANTÉ IA</h2>
                <div style='background:rgba(255,255,255,0.05); color:#FFFFFF; padding:6px 14px; border-radius:30px; font-size:0.75rem; font-weight:800; border:1px solid rgba(255,255,255,0.1);'>MOTEUR v2.4</div>
            </div>
            <p style='color:{subtext}; font-size:0.9rem; margin-top:10px;'>Analyse prédictive basée sur les symptômes et l'historique.</p>
        """, unsafe_allow_html=True)
        st.divider()
        
        ms, labels, conseils_prev = get_sante()
        
        # Layout Principal
        c_main, c_res = st.columns([1.6, 1])
        
        with c_main:
            st.markdown("### Paramètres Patient")
            c1, c2 = st.columns(2)
            with c1: age = st.number_input("Âge (années)", min_value=0, max_value=120, value=35, step=1)
            with c2: dur_s = st.selectbox("Durée des symptômes", options=["< 24h", "1-3 jours", "3-7 jours", "> 7 jours"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### Symptômes")
            
            t1, t2, t3 = st.tabs(["Général", "Respiratoire", "Digestif/Autre"])
            
            with t1:
                c_a, c_b = st.columns(2)
                with c_a: 
                    fievre = st.toggle("Fièvre (> 38°C)")
                    fat = st.toggle("Fatigue Intense")
                with c_b: 
                    friss = st.toggle("Frissons")
                    vert = st.toggle("Vertiges")
            
            with t2:
                c_a, c_b = st.columns(2)
                with c_a: 
                    toux = st.toggle("Toux Sèche")
                    ess = st.toggle("Essoufflement")
                with c_b: 
                    gorge = st.toggle("Maux de Gorge")
                    odorat = st.toggle("Perte Odorat/Goût")
            
            with t3:
                c_a, c_b = st.columns(2)
                with c_a: 
                    nau = st.toggle("Nausées")
                    diar = st.toggle("Diarrhée")
                with c_b: 
                    tete = st.toggle("Maux de Tête")
                    thor = st.toggle("Douleur Thoracique")
                    mus = st.toggle("Douleurs Musculaires")
                    pal = st.toggle("Palpitations")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            go_scan = st.button("LANCER L'ANALYSE DIAGNOSTIQUE", type="primary", use_container_width=True)

        with c_res:
            if go_scan:
                # Mapping des symptômes
                symptomes_map = [fievre, toux, fat, tete, gorge, nau, thor, ess, diar, friss, odorat, mus, pal, vert]
                nb_symptomes = sum(symptomes_map)
                
                if nb_symptomes == 0:
                    st.warning("Veuillez sélectionner au moins un symptôme.")
                else:
                    with st.spinner("Analyse des biomarqueurs en cours..."):
                        time.sleep(1.5) # Simulation temps de calcul
                        
                        # Création DataFrame pour le modèle
                        feat = pd.DataFrame([{"fievre":int(fievre),"toux":int(toux),"fatigue":int(fat),"maux_tete":int(tete),"douleur_gorge":int(gorge),"nausees":int(nau),"douleur_thorax":int(thor),"essoufflement":int(ess),"diarrhee":int(diar),"frissons":int(friss),"perte_odorat":int(odorat),"douleurs_musculaires":int(mus),"palpitations":int(pal),"vertiges":int(vert)}])
                        
                        pred = ms.predict(feat)[0]
                        proba = ms.predict_proba(feat)[0]
                        diag = labels[pred]
                        conf = proba[pred] * 100
                        
                        # Logique d'urgence
                        is_urgent = "cardiaque" in diag.lower() or "covid" in diag.lower() or conf < 60
                        color_res = "#FFFFFF" # Monochromatic
                        
                        # SVG Icons
                        svg_alert = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>"""
                        svg_health = """<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/><path d="M12 5 9.04 11l6.22-2.22a.56.56 0 0 1 .63.95l-5.63 3.4L15 18"/></svg>"""
                        icon_res = svg_alert if is_urgent else svg_health
                        
                        # Affichage Résultat
                        st.markdown(f"""
                        <div class='k-card' style='border-top:3px solid {color_res};text-align:center;padding:30px'>
                            <div style='margin-bottom:12px;color:{color_res}'>{icon_res}</div>
                            <h3 style='color:{color_res};margin:0;text-transform:uppercase;font-weight:800'>{diag}</h3>
                            <div style='height:1px;background:#1C1F2E;margin:16px 0'></div>
                            <div class='k-label' style='margin-bottom:6px'>FIABILITÉ IA</div>
                            <div class='k-mono' style='font-size:2rem;font-weight:800;color:{color_res}'>{conf:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Section Conseils
                        st.markdown("#### RECOMMANDATIONS")
                        if diag in conseils_prev:
                            for c in conseils_prev[diag]:
                                st.info(f"{c}")
                        else:
                            st.info("Consultez un médecin pour un avis professionnel.")
                            
                        if is_urgent:
                            st.error("SITUATION CRITIQUE : CONTACTEZ LES SECOURS (15)")
                        
                        # Rapport PDF
                        try:
                            from rapport_pdf import generer_rapport_sante
                            all_sym_names = ["Fièvre","Toux","Fatigue","Maux de tête","Maux de gorge","Nausées","Douleur thoracique","Essoufflement","Diarrhée","Frissons","Perte odorat","Douleurs musculaires","Palpitations","Vertiges"]
                            active_syms = [name for name, val in zip(all_sym_names, symptomes_map) if val]
                            
                            pdf_data = {
                                "age": age, "duree_symptomes": dur_s,
                                "symptomes": active_syms,
                                "diagnostic": diag, "confiance": conf, "urgent": is_urgent,
                                "utilisateur": st.session_state.username if "username" in st.session_state else "Guest",
                                "role": "User"
                            }
                            pdf_bytes = generer_rapport_sante(pdf_data)
                            st.download_button("📥 TÉLÉCHARGER RAPPORT", pdf_bytes, file_name=f"rapport_{st.session_state.username}.pdf", mime="application/pdf", use_container_width=True)
                            
                            # Log History
                            log_entry = {
                                "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "Module": "Sante",
                                "Resultat": diag,
                                "Confiance": f"{conf:.0f}%",
                                "Utilisateur": st.session_state.username,
                                "Detail": f"Age {age}, {nb_symptomes} sympt."
                            }
                            st.session_state.historique.append(log_entry)
                            
                        except Exception as e:
                            st.warning("Service PDF indisponible momentanément.")
            
            else:
                # Placeholder state (SVG Icon instead of Emoji)
                st.markdown("""
                <div class='k-card' style='text-align:center;padding:60px 30px'>
                    <div style='margin-bottom:16px; opacity:0.6'>
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
                            <path d="M12 5 9.04 11l6.22-2.22a.56.56 0 0 1 .63.95l-5.63 3.4L15 18"/>
                        </svg>
                    </div>
                    <p style='font-size:1.1rem;font-weight:600;margin-bottom:6px'>En attente de données...</p>
                    <p class='k-subtext' style='font-size:.85rem'>Veuillez remplir le formulaire à gauche.</p>
                </div>
                """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    #  ASSISTANT AI
    # ═══════════════════════════════════════════════════════════════
    elif page == "Assistant":
        st.markdown("## KOTIGHI ASSISTANT", unsafe_allow_html=True)
        st.divider()

        # Conteneur de chat
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                role = message["role"]
                content = message["content"]
                if role == "user":
                    st.markdown(f"""
                    <div style='display:flex; justify-content:flex-end; margin-bottom:12px;'>
                        <div style='background:rgba(255,255,255,0.03); padding:14px 20px; border-radius:18px 18px 4px 18px; max-width:80%; border:1px solid rgba(255,255,255,0.08); color:#E2E8F0; font-size:0.9rem;'>
                            {content}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='display:flex; justify-content:flex-start; margin-bottom:12px;'>
                        <div style='background:rgba(255, 255, 255, 0.05); padding:14px 20px; border-radius:18px 18px 18px 4px; max-width:80%; border:1px solid rgba(255, 255, 255, 0.1); color:#FFFFFF; font-size:0.9rem;'>
                            <b style='font-size:0.7rem; text-transform:uppercase; letter-spacing:1px; display:block; margin-bottom:4px;'>KOTIGHI AI</b>
                            {content}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        # Zone d'input (en bas) fixée simulée
        with st.form("chat_input", clear_on_submit=True):
            user_input = st.text_input("Posez votre question...", placeholder="Ex: Risques de sécurité sur 192.168.1.1 ou Symptômes grippe")
            submitted = st.form_submit_button("ENVOYER")
            
            if submitted and user_input:
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Logique de réponse simple
                q = user_input.lower()
                response = ""
                
                if "réseau" in q or "ip" in q or "attaque" in q or "cyber" in q:
                    response = "ANALYSE : Flux stable. 3 IPs sous surveillance. Voulez-vous un scan profond ?"
                elif "santé" in q or "docteur" in q or "symptôme" in q or "malade" in q:
                    response = "ANALYSE : Je peux aider au diagnostic. Avez-vous de la fièvre ?"
                elif "qui es-tu" in q:
                    response = "INFO : Assistant KOTIGHI AI, expert en cybersécurité et santé."
                else:
                    response = "INFO : Précisez votre demande (Cyber ou Santé)."
                
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()

    # ═══════════════════════════════════════════════════════════════
    #  GESTION
    # ═══════════════════════════════════════════════════════════════
    elif page == "Gestion":
        st.markdown("## GESTION", unsafe_allow_html=True)
        st.divider()
        
        st.markdown("### Utilisateurs")
        df_u = pd.DataFrame([{"Login":k,"Nom":v["nom"],"Rôle":v["role"],"Modules":", ".join(v["acces"])} for k,v in USERS.items()])
        st.dataframe(df_u,use_container_width=True,hide_index=True)
        st.markdown("<br>",unsafe_allow_html=True)
        
        st.markdown("### Logs Globaux")
        if st.session_state.historique:
            df_global = pd.DataFrame(st.session_state.historique[::-1])
            if "IP" in df_global.columns:
                df_global["IP"] = df_global["IP"].apply(mask_data)
            if "Utilisateur" in df_global.columns:
                df_global["Utilisateur"] = df_global["Utilisateur"].apply(mask_data)
                
            st.dataframe(df_global, use_container_width=True, hide_index=True)
        else:
            st.info("Aucun log.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("Pour ajouter un utilisateur : ajouter une entrée dans USERS.")

    # --- RENDER BOTTOM NAVIGATION (VISUAL ONLY) ---
    st.markdown(f"""
        <div class="bottom-nav">
            {"".join([f'<div class="nav-item {"active" if st.session_state.current_page == p else ""}"><div class="nav-label">{p}</div></div>' for p in pages])}
        </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── POINT D'ENTREE ────────────────────────────────────────────────
if not st.session_state.connecte:
    # On masque la sidebar sur la page de login
    st.markdown("""<style>
    [data-testid="stSidebar"] { display: none; }
    </style>""", unsafe_allow_html=True)
    apply_theme()
    page_login()
else:
    app()