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
    "admin":    {"hash":h("kotighi2024"),"role":"Administrateur","nom":"Admin Principal",   "acces":["Dashboard","Cybersecurite","Sante","Gestion"]},
    "analyste": {"hash":h("analyse123"), "role":"Analyste Cyber", "nom":"Jean Dupont",      "acces":["Dashboard","Cybersecurite"]},
    "medecin":  {"hash":h("sante456"),   "role":"Medecin",        "nom":"Dr. House",        "acces":["Dashboard","Sante"]},
}

def verifier(login, mdp):
    l = login.strip().lower()
    if l in USERS and USERS[l]["hash"] == h(mdp): return USERS[l]
    return None

for k,v in {"connecte":False,"utilisateur":None,"login_nom":None,"tentatives":0,"historique":[],"theme":"Sombre"}.items():
    if k not in st.session_state: st.session_state[k] = v

# ── THEME CSS ────────────────────────────────────────────────────
def get_logo_html(fill_color):
    try:
        with open("logo.svg", "r") as f:
            svg = f.read()
        # Injection couleur et style responsive
        svg = svg.replace("<svg", f'<svg fill="{fill_color}" style="width:100%;height:auto;"')
        return svg
    except FileNotFoundError:
        return ""

def apply_theme():
    is_dark = st.session_state.theme == "Sombre"
    # — Premium Color Palette —
    bg       = "#06070A" if is_dark else "#F1F5F9"
    bg2      = "#0D0E14" if is_dark else "#E2E8F0"
    text     = "#E2E8F0" if is_dark else "#1E293B"
    card     = "#0F1117" if is_dark else "#FFFFFF"
    border   = "#1C1F2E" if is_dark else "#CBD5E1"
    subtext  = "#64748B"
    primary  = "#00E5FF"
    accent   = "#8B5CF6"
    danger   = "#EF4444"
    warning  = "#F59E0B"
    success  = "#10B981"
    sidebar_bg = "#0A0B10" if is_dark else "#F8FAFC"

    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    /* ═══ KEYFRAMES ═══ */
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(12px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes slideInLeft {{ from {{ opacity:0; transform:translateX(-20px); }} to {{ opacity:1; transform:translateX(0); }} }}
    @keyframes pulseGlow {{ 0%,100% {{ box-shadow:0 0 8px {primary}30; }} 50% {{ box-shadow:0 0 20px {primary}50; }} }}
    @keyframes shimmer {{ 0% {{ background-position:-200% 0; }} 100% {{ background-position:200% 0; }} }}
    @keyframes blink {{ 50% {{ opacity:.4; }} }}

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
        animation: slideInLeft .4s ease-out;
    }}

    /* ═══ METRIC CARDS ═══ */
    [data-testid="metric-container"] {{
        background: {card} !important;
        border: 1px solid {border};
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,.12), 0 1px 2px rgba(0,0,0,.08);
        transition: all .3s cubic-bezier(.4,0,.2,1);
        animation: fadeIn .5s ease-out;
    }}
    [data-testid="metric-container"]:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 28px rgba(0,0,0,.2), 0 0 0 1px {primary}20;
        border-color: {primary}40;
    }}
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {{
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: .8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: {subtext} !important;
    }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 1.6rem !important;
        color: {text} !important;
    }}
    [data-testid="metric-container"] [data-testid="stMetricDelta"] {{
        font-family: 'JetBrains Mono', monospace;
        font-size: .75rem;
    }}

    /* ═══ INPUTS ═══ */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {{
        background: {bg2} !important;
        color: {text} !important;
        border: 1px solid {border} !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-family: 'Inter', sans-serif;
        font-size: .9rem;
        transition: all .25s ease;
    }}
    .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
        border-color: {primary} !important;
        box-shadow: 0 0 0 3px {primary}15 !important;
        outline: none !important;
    }}
    .stSelectbox > div > div {{
        background: {bg2} !important;
        border: 1px solid {border} !important;
        border-radius: 10px !important;
    }}

    /* ═══ BUTTONS ═══ */
    .stButton > button {{
        background: {primary} !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 10px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: .85rem;
        letter-spacing: .5px;
        padding: .65rem 1.5rem;
        transition: all .3s cubic-bezier(.4,0,.2,1);
        text-transform: uppercase;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 25px {primary}35;
        filter: brightness(1.1);
    }}
    .stButton > button:active {{
        transform: translateY(0);
        box-shadow: 0 2px 8px {primary}20;
    }}

    /* ═══ TYPOGRAPHY ═══ */
    h1 {{
        color: {text} !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 800 !important;
        font-size: 2.2rem !important;
        letter-spacing: -1px;
    }}
    h2 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        color: {text} !important;
        font-size: 1.4rem !important;
        letter-spacing: -.5px;
    }}
    h3, h4 {{
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        color: {text} !important;
    }}

    /* ═══ TABS ═══ */
    .stTabs [data-baseweb="tab-list"] {{
        background: {card};
        border-radius: 12px;
        padding: 4px;
        border: 1px solid {border};
        gap: 4px;
    }}
    .stTabs [data-baseweb="tab"] {{
        color: {subtext} !important;
        font-family: 'JetBrains Mono', monospace;
        font-size: .78rem;
        font-weight: 500;
        border-radius: 8px;
        padding: 8px 16px;
        text-transform: uppercase;
        letter-spacing: .5px;
    }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: {primary}15 !important;
        color: {primary} !important;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(0,0,0,.15);
    }}
    .stTabs [data-baseweb="tab-highlight"] {{
        background-color: transparent !important;
    }}

    /* ═══ DATAFRAMES ═══ */
    [data-testid="stDataFrame"] {{
        border: 1px solid {border};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ═══ DIVIDER ═══ */
    hr {{ border-color: {border} !important; opacity: .5; }}

    /* ═══ PROGRESS BARS ═══ */
    .stProgress > div > div {{
        background: {primary} !important;
        border-radius: 8px;
    }}

    /* ═══ CUSTOM COMPONENTS ═══ */
    .k-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: {primary}10;
        border: 1px solid {primary}30;
        border-radius: 20px;
        padding: 5px 14px;
        font-family: 'JetBrains Mono', monospace;
        font-size: .7rem;
        font-weight: 600;
        color: {primary};
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }}
    .k-card {{
        background: {card};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 24px;
        transition: all .3s ease;
        animation: fadeIn .5s ease-out;
    }}
    .k-card:hover {{
        border-color: {primary}30;
        box-shadow: 0 8px 30px rgba(0,0,0,.15);
    }}
    .k-card-accent {{
        background: {card};
        border: 1px solid {border};
        border-left: 3px solid {primary};
        border-radius: 12px;
        padding: 20px 24px;
        transition: all .3s ease;
    }}
    .k-card-accent:hover {{
        border-left-color: {accent};
        box-shadow: 0 4px 16px rgba(0,0,0,.12);
    }}
    .k-alert-danger {{
        background: {danger}08;
        border: 1px solid {danger}25;
        border-left: 3px solid {danger};
        border-radius: 10px;
        padding: 14px 18px;
        color: {danger};
        font-family: 'JetBrains Mono', monospace;
        font-size: .85rem;
        animation: fadeIn .4s ease-out;
    }}
    .k-alert-success {{
        background: {success}08;
        border: 1px solid {success}25;
        border-left: 3px solid {success};
        border-radius: 10px;
        padding: 14px 18px;
        color: {success};
        font-family: 'JetBrains Mono', monospace;
        font-size: .85rem;
        animation: fadeIn .4s ease-out;
    }}
    .k-alert-warning {{
        background: {warning}08;
        border: 1px solid {warning}25;
        border-left: 3px solid {warning};
        border-radius: 10px;
        padding: 14px 18px;
        color: {warning};
        font-family: 'JetBrains Mono', monospace;
        font-size: .85rem;
    }}
    .k-info {{
        background: {accent}08;
        border: 1px solid {accent}20;
        border-radius: 12px;
        padding: 16px 20px;
        color: {accent};
        font-family: 'JetBrains Mono', monospace;
        font-size: .82rem;
        line-height: 1.7;
    }}
    .k-mono {{ font-family: 'JetBrains Mono', monospace; }}
    .k-subtext {{ color: {subtext}; font-size: .85rem; }}
    .k-label {{
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: .7rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: {subtext};
        margin-bottom: 4px;
    }}
    /* SOC TERMINAL STYLES */
    .soc-panel {{
        background: {card};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        animation: fadeIn .5s ease-out;
    }}
    .soc-header {{
        font-family: 'JetBrains Mono', monospace;
        font-size: .7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: {subtext};
        border-bottom: 1px solid {border};
        padding-bottom: 10px;
        margin-bottom: 16px;
    }}
    .status-dot {{
        height: 8px; width: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 6px;
    }}
    .dot-green {{ background: {success}; box-shadow: 0 0 8px {success}80; }}
    .dot-red {{ background: {danger}; box-shadow: 0 0 8px {danger}80; animation: blink 1.2s ease-in-out infinite; }}
    .dot-yellow {{ background: {warning}; box-shadow: 0 0 8px {warning}60; }}
    /* CLINIC STYLES */
    .clinic-card {{
        background: {card};
        border: 1px solid {border};
        border-left: 3px solid {primary};
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 16px;
        transition: all .3s ease;
        animation: fadeIn .5s ease-out;
    }}
    .clinic-card:hover {{
        box-shadow: 0 6px 24px rgba(0,0,0,.15);
        border-left-color: {accent};
    }}
    /* USER PROFILE CARD */
    .k-profile {{
        background: {card};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 20px;
    }}
    .k-profile-name {{
        font-weight: 700;
        color: {text};
        font-size: .95rem;
        margin-bottom: 2px;
    }}
    .k-profile-role {{
        font-family: 'JetBrains Mono', monospace;
        font-size: .7rem;
        font-weight: 600;
        color: {primary};
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    /* FEATURE CARDS */
    .feature-card {{
        background: {card};
        border: 1px solid {border};
        border-radius: 14px;
        padding: 20px;
        transition: all .3s cubic-bezier(.4,0,.2,1);
        cursor: pointer;
    }}
    .feature-card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 12px 28px rgba(0,0,0,.18);
        border-color: {primary}40;
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

# ── PAGE LOGIN ────────────────────────────────────────────────────
def page_login():
    if "auth_mode" not in st.session_state: st.session_state.auth_mode = "Connexion"
    
    st.markdown("""<style>
    div[role="radiogroup"] { justify-content: center; }
    </style>""", unsafe_allow_html=True)

    mode = st.radio("Action", ["Connexion", "Inscription"], 
                    index=0 if st.session_state.auth_mode == "Connexion" else 1,
                    horizontal=True, label_visibility="collapsed", key="auth_mode_selector")
    st.session_state.auth_mode = mode
    
    # LOGO
    _, c_l, _ = st.columns([1, 0.8, 1])
    with c_l:
        logo_color = "#E2E8F0" if st.session_state.theme == "Sombre" else "#1E293B"
        st.markdown(get_logo_html(logo_color), unsafe_allow_html=True)
        
    st.markdown(f"""<div style='text-align:center;padding:0 0 16px'>
        <div class='k-badge' style='margin:8px auto;display:inline-flex'>{st.session_state.auth_mode.upper()}</div>
    </div>""", unsafe_allow_html=True)
    
    _,col,_ = st.columns([1,1.2,1])
    with col:
        if st.session_state.auth_mode == "Connexion":
            st.markdown("""<div class='k-card' style='padding:32px 28px;margin-top:12px'>
                <div style='font-size:1.1rem;font-weight:700;margin-bottom:4px'>🔐 Connexion</div>
                <div class='k-subtext' style='font-family:JetBrains Mono,monospace;font-size:.75rem;margin-bottom:20px'>Identifiez-vous pour accéder à la plateforme</div>
            </div>""", unsafe_allow_html=True)
            if st.session_state.tentatives >= 5:
                st.markdown("<div class='k-alert-danger'>⛔ Trop de tentatives. Compte bloqué.</div>", unsafe_allow_html=True)
                return
            login    = st.text_input("Identifiant", placeholder="Votre login")
            password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
            
            if st.button("SE CONNECTER", type="primary", use_container_width=True):
                user = verifier(login, password)
                if user:
                    st.session_state.connecte = True
                    st.session_state.utilisateur = user
                    st.session_state.login_nom = login.lower()
                    st.session_state.tentatives = 0
                    st.success("Connexion réussie."); time.sleep(0.8); st.rerun()
                else:
                    st.session_state.tentatives += 1
                    st.markdown("<div class='k-alert-danger'>Identifiant ou mot de passe incorrect.</div>", unsafe_allow_html=True)
        
        else:
            st.markdown("""<div class='k-card' style='padding:32px 28px;margin-top:12px'>
                <div style='font-size:1.1rem;font-weight:700;margin-bottom:4px'>📝 Inscription</div>
                <div class='k-subtext' style='font-family:JetBrains Mono,monospace;font-size:.75rem;margin-bottom:20px'>Créez votre compte personnel</div>
            </div>""", unsafe_allow_html=True)
            new_login = st.text_input("Nouvel Identifiant")
            new_name  = st.text_input("Nom Complet")
            new_role  = st.selectbox("Rôle", ["Analyste Cyber", "Medecin"])
            new_pass  = st.text_input("Nouveau Mot de passe", type="password")
            if st.button("CRÉER MON COMPTE", type="primary", use_container_width=True):
                if new_login and new_pass and new_name:
                    is_strong, msg_strong = check_password_strength(new_pass)
                    if not is_strong:
                        st.markdown(f"<div class='k-alert-danger'>{msg_strong}</div>", unsafe_allow_html=True)
                    else:
                        USERS[new_login.lower()] = {
                            "hash": h(new_pass),
                            "role": new_role,
                            "nom": new_name,
                            "acces": ["Dashboard", "Cybersecurite"] if new_role == "Analyste Cyber" else ["Dashboard", "Sante"]
                        }
                        st.markdown("<div class='k-alert-success'>✅ Compte créé avec succès ! Connectez-vous.</div>", unsafe_allow_html=True)
                        st.session_state.auth_mode = "Connexion"
                        time.sleep(1.5)
                        st.rerun()
                else:
                    st.error("Veuillez remplir tous les champs.")

        st.markdown("""<div style='margin-top:24px;text-align:center'>
            <div class='k-subtext' style='font-family:JetBrains Mono,monospace;font-size:.72rem'>
                Comptes démo :<br>
                <span style='color:#00E5FF'>admin</span> / kotighi2024 &nbsp;·&nbsp; 
                <span style='color:#00E5FF'>analyste</span> / analyse123 &nbsp;·&nbsp; 
                <span style='color:#00E5FF'>medecin</span> / sante456
            </div>
        </div>""", unsafe_allow_html=True)

# ── APPLICATION PRINCIPALE ────────────────────────────────────────
def app():
    # SIDEBAR
    with st.sidebar:
        st.session_state.theme = st.selectbox("Thème", ["Sombre", "Clair"], index=0 if st.session_state.theme == "Sombre" else 1)
        apply_theme()
        
        # LOGO
        c_logo, _ = st.columns([1, 0.1])
        with c_logo:
            logo_color = "#E2E8F0" if st.session_state.theme == "Sombre" else "#1E293B"
            st.markdown(get_logo_html(logo_color), unsafe_allow_html=True)
            
        st.markdown("""<div style='text-align:center;padding-bottom:20px'>
            <div class='k-badge' style='margin:6px auto;display:inline-flex'>V3.0 · ENTERPRISE</div>
        </div>""", unsafe_allow_html=True)
        
        # User Profile Card
        user = st.session_state.utilisateur
        st.markdown(f"""
        <div class='k-profile'>
            <div class='k-label'>Connecté en tant que</div>
            <div class='k-profile-name'>👤 {user['nom']}</div>
            <div class='k-profile-role'>{user['role']}</div>
        </div>
        """, unsafe_allow_html=True)

        pages = [p for p in user["acces"] if p in ["Dashboard", "Cybersecurite", "Sante", "Gestion"]]
        page = st.radio("Navigation", pages, label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.connecte = False
            st.rerun()

    # ═══════════════════════════════════════════════════════════════
    #  DASHBOARD
    # ═══════════════════════════════════════════════════════════════
    if page == "Dashboard":
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"""
            <div style='margin-top:0'>
                <div class='k-badge'>TABLEAU DE BORD CENTRALISÉ</div>
                <h1 style='margin-top:12px;font-size:2rem!important'>Bienvenue, {user['nom']}</h1>
                <p class='k-subtext' style='font-size:.95rem;line-height:1.5;margin-bottom:20px'>
                    Surveillance active des systèmes et état de santé global.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            if lottie_scan:
                st_lottie(lottie_scan, height=150, key="hero_anim_mini")

        st.divider()

        # KPI CARDS
        np.random.seed(int(time.time()))
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Connexions analysées","12 847","+234")
        with c2: st.metric("Attaques bloquées","1 203","+18")
        with c3: st.metric("Diagnostics santé","452","+12")
        with c4: st.metric("Fiabilité IA","99.2%","+0.1%")
        
        st.markdown("<br>",unsafe_allow_html=True)
        
        # CHARTS + QUICK ACCESS
        cl,cr = st.columns([2, 1])
        
        with cl:
            st.markdown("#### 📈 Activité Temps Réel (24h)")
            hours = list(range(24))
            activity_data = pd.DataFrame({
                "Heure": hours,
                "Requêtes": np.random.randint(100, 500, 24),
                "Menaces": np.random.randint(0, 50, 24)
            })
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=hours, y=activity_data["Requêtes"], name="Requêtes",
                line=dict(color="#00E5FF", width=2), fill="tozeroy",
                fillcolor="rgba(0,229,255,0.05)"))
            fig_line.add_trace(go.Scatter(x=hours, y=activity_data["Menaces"], name="Menaces",
                line=dict(color="#EF4444", width=2), fill="tozeroy",
                fillcolor="rgba(239,68,68,0.05)"))
            fig_line.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=320, margin=dict(t=20, b=30, l=40, r=20),
                legend=dict(orientation="h", y=1.12, font=dict(family="JetBrains Mono", size=11)),
                xaxis=dict(showgrid=False, color="#64748B", title=""),
                yaxis=dict(showgrid=True, gridcolor="#1C1F2E20", color="#64748B", title=""),
                font=dict(family="Inter", color="#64748B")
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with cr:
            st.markdown("#### 🚀 Accès Rapide")
            if "Cybersecurite" in user["acces"]:
                st.markdown("""
                <div class='feature-card' style='margin-bottom:12px'>
                    <div style='font-size:1.5rem;margin-bottom:8px'>🛡️</div>
                    <div style='font-weight:700;color:#00E5FF;margin-bottom:4px;font-size:.95rem'>Module Cyber</div>
                    <div class='k-subtext' style='font-size:.8rem'>Lancer un scan réseau</div>
                </div>
                """, unsafe_allow_html=True)
            
            if "Sante" in user["acces"]:
                st.markdown("""
                <div class='feature-card'>
                    <div style='font-size:1.5rem;margin-bottom:8px'>🩺</div>
                    <div style='font-weight:700;color:#8B5CF6;margin-bottom:4px;font-size:.95rem'>Module Santé</div>
                    <div class='k-subtext' style='font-size:.8rem'>Nouveau diagnostic</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>",unsafe_allow_html=True)
        
        # RECENT ACTIVITY
        st.markdown("#### 🕒 Dernières Activités")
        if st.session_state.historique:
            df_hist = pd.DataFrame(st.session_state.historique[::-1]).head(5)
            st.dataframe(df_hist,use_container_width=True,hide_index=True)
        else:
            st.info("Aucune activité récente.")
    
    # ═══════════════════════════════════════════════════════════════
    #  CYBERSECURITE — SOC TERMINAL
    # ═══════════════════════════════════════════════════════════════
    elif page == "Cybersecurite":
        st.markdown("## <span style='color:#00E5FF'>//</span> SOC TERMINAL <span class='k-badge' style='vertical-align:middle;margin-left:8px'>v3.1 · LIVE</span>", unsafe_allow_html=True)
        
        m_rf, m_gb, sc = get_cyber()
        
        # Initialisation Watchlist
        if "watchlist" not in st.session_state: st.session_state.watchlist = []
        
        col_main, col_side = st.columns([3, 1])
        
        with col_main:
            # ONGLETS FONCTIONNELS
            tab1, tab2 = st.tabs(["SCAN MANUEL / BATCH", "LIVE MONITOR"])
            
            with tab1:
                st.markdown("<div class='soc-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='soc-header'>CIBLE(S) D'ANALYSE</div>", unsafe_allow_html=True)
                
                # Gestion dynamique des champs d'IP
                if "ip_count" not in st.session_state: st.session_state.ip_count = 1
                
                # Boutons +/- pour ajouter/retirer des champs
                c_add, c_rem, _ = st.columns([1, 1, 4])
                if c_add.button("➕ Ajouter IP", key="add_ip"): 
                    st.session_state.ip_count += 1
                    st.rerun()
                if c_rem.button("➖ Retirer", key="rem_ip") and st.session_state.ip_count > 1: 
                    st.session_state.ip_count -= 1
                    st.rerun()
                
                ips_list = []
                cols = st.columns(3) # Grille de 3 colonnes pour les inputs
                for i in range(st.session_state.ip_count):
                    with cols[i % 3]:
                        val = st.text_input(f"IP Cible #{i+1}", key=f"ip_input_{i}", placeholder="192.168.x.x")
                        if val: ips_list.append(val)
                
                st.markdown("---")
                c1, c2, c3 = st.columns(3)
                with c1: req = st.number_input("Req/min (Simulé)", 0, 10000, 150)
                with c2: ports = st.number_input("Ports ouverts (Simulé)", 0, 1000, 5)
                with c3: terr = st.number_input("Taux erreur (Simulé)", 0.0, 1.0, 0.01)
                
                col_act, col_add = st.columns([1, 1])
                with col_act:
                    go_scan = st.button("LANCER LE SCAN BATCH", type="primary", use_container_width=True)
                with col_add:
                    add_watch = st.button("AJOUTER À LA SURVEILLANCE", use_container_width=True)
                
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
                        
                        verdict = "CRITIQUE" if score > 0.8 else ("SUSPECT" if score > 0.5 else "SECURE")
                        results.append({"IP": ip, "Status": verdict, "Score": f"{score*100:.1f}%", "Ports": sim_ports})
                        
                        time.sleep(0.1) # Effet scan rapide
                        progress_bar.progress((i + 1) / len(ips))
                        
                    status_text.empty()
                    progress_bar.empty()
                    
                    # Affichage style Terminal
                    st.markdown("<div class='soc-header'>RÉSULTATS DU SCAN</div>", unsafe_allow_html=True)
                    df_res = pd.DataFrame(results)
                    
                    # Style conditionnel
                    def highlight_status(val):
                        color = '#ff4757' if val == 'CRITIQUE' else ('#ffa502' if val == 'SUSPECT' else '#00f5c4')
                        return f'color: {color}; font-weight: bold'
                        
                    st.dataframe(df_res.style.applymap(highlight_status, subset=['Status']), use_container_width=True)
                
                if add_watch and ips_list:
                    new_ips = [ip.strip() for ip in ips_list if ip.strip()]
                    for ip in new_ips:
                        if ip not in [w["ip"] for w in st.session_state.watchlist]:
                            st.session_state.watchlist.append({"ip": ip, "added_at": datetime.datetime.now().strftime("%H:%M"), "status": "PENDING"})
                    st.success(f"{len(new_ips)} cible(s) ajoutée(s) à la surveillance continue.")
                
                st.markdown("</div>", unsafe_allow_html=True)

            with tab2:
                st.markdown("<div class='soc-panel'>", unsafe_allow_html=True)
                st.markdown("<div class='soc-header'>SURVEILLANCE ACTIVE (LIVE MONITOR)</div>", unsafe_allow_html=True)
                
                if not st.session_state.watchlist:
                    st.info("Aucune cible sous surveillance. Ajoutez des IPs depuis l'onglet Scan.")
                else:
                    # Simulation de mise à jour temps réel
                    col_metrics = st.columns(4)
                    col_metrics[0].metric("Cibles Actives", len(st.session_state.watchlist))
                    col_metrics[1].metric("Alertes (1h)", np.random.randint(0, 5))
                    col_metrics[2].metric("Bande Passante", f"{np.random.randint(50, 500)} Mbps")
                    
                    st.markdown("---")
                    
                    for target in st.session_state.watchlist:
                        # Simulation état
                        is_threat = np.random.random() > 0.8
                        status_color = "dot-red" if is_threat else "dot-green"
                        status_txt = "MENACE DÉTECTÉE" if is_threat else "NORMAL"
                        traffic = np.random.randint(100, 2000)
                        
                        cols = st.columns([0.5, 2, 1, 1, 1])
                        with cols[0]: st.markdown(f"<div class='status-dot {status_color}'></div>", unsafe_allow_html=True)
                        with cols[1]: st.markdown(f"<span style='font-family:monospace;font-size:1.1rem'>{target['ip']}</span>", unsafe_allow_html=True)
                        with cols[2]: st.caption(f"Trafic: {traffic} req/m")
                        with cols[3]: st.markdown(f"<span style='color:{'#EF4444' if is_threat else '#10B981'}'>{status_txt}</span>", unsafe_allow_html=True)
                        with cols[4]: 
                            if st.button("STOP", key=f"del_{target['ip']}"):
                                st.session_state.watchlist.remove(target)
                                st.rerun()
                        st.markdown("<div style='border-bottom:1px solid #1C1F2E;margin:5px 0'></div>", unsafe_allow_html=True)
                        
                        if is_threat:
                            st.toast(f"🚨 ALERTE SUR {target['ip']}", icon="🔥")
                
                st.markdown("</div>", unsafe_allow_html=True)

        with col_side:
            st.markdown("<div class='soc-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='soc-header'>FLUX D'ÉVÉNEMENTS</div>", unsafe_allow_html=True)
            # Logs fictifs défilants
            events = [
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] SCAN BLOCK 192.168.1.45",
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] SSH FAIL 10.0.0.12",
                f"[{datetime.datetime.now().strftime('%H:%M:%S')}] FW UPDATE SUCCESS",
                f"[{(datetime.datetime.now()-datetime.timedelta(minutes=1)).strftime('%H:%M:%S')}] API KOTIGHI CONNECTED"
            ]
            for evt in events:
                st.markdown(f"<div class='k-mono' style='font-size:0.72rem;color:#00E5FF;margin-bottom:6px'>{evt}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='soc-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='soc-header'>ÉTAT SYSTÈME</div>", unsafe_allow_html=True)
            st.progress(88, text="CPU LOAD")
            st.progress(45, text="RAM USAGE")
            st.progress(12, text="NETWORK I/O")
            st.markdown("</div>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    #  SANTÉ — MODULE CLINIQUE
    # ═══════════════════════════════════════════════════════════════
    elif page == "Sante":
        st.markdown("## <span style='color:#00E5FF'>//</span> MODULE CLINIQUE <span class='k-badge' style='vertical-align:middle;margin-left:8px'>v2.4 · IA</span>", unsafe_allow_html=True)
        st.markdown("<p class='k-subtext k-mono' style='font-size:.9rem'>SYSTÈME D'AIDE AU DIAGNOSTIC MÉDICAL PAR IA</p>", unsafe_allow_html=True)
        st.divider()
        
        ms, labels, conseils_prev = get_sante()
        
        # Layout Principal
        c_main, c_res = st.columns([1.6, 1])
        
        with c_main:
            st.markdown("<div class='clinic-card'>", unsafe_allow_html=True)
            st.markdown("#### PARAMÈTRES PATIENT")
            c1, c2 = st.columns(2)
            with c1: age = st.slider("Âge", 0, 120, 35)
            with c2: dur_s = st.select_slider("Durée des symptômes", options=["< 24h", "1-3 jours", "3-7 jours", "> 7 jours"])
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='clinic-card'>", unsafe_allow_html=True)
            st.markdown("#### ANALYSE SYMPTOMATIQUE")
            
            t1, t2, t3 = st.tabs(["GÉNÉRAL", "RESPIRATOIRE", "DIGESTIF & AUTRES"])
            
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
                        color_res = "#EF4444" if is_urgent else ("#F59E0B" if conf < 80 else "#10B981")
                        icon_res = "🚨" if is_urgent else "🩺"
                        
                        # Affichage Résultat
                        st.markdown(f"""
                        <div class='k-card' style='border-top:3px solid {color_res};text-align:center;padding:30px'>
                            <div style='font-size:3.5rem;margin-bottom:12px'>{icon_res}</div>
                            <h3 style='color:{color_res};margin:0;text-transform:uppercase;font-weight:800'>{diag}</h3>
                            <div style='height:1px;background:#1C1F2E;margin:16px 0'></div>
                            <div class='k-label' style='margin-bottom:6px'>FIABILITÉ IA</div>
                            <div class='k-mono' style='font-size:2rem;font-weight:800;color:{color_res}'>{conf:.1f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Section Conseils
                        st.markdown("#### 💡 RECOMMANDATIONS")
                        if diag in conseils_prev:
                            for c in conseils_prev[diag]:
                                st.info(f"{c}")
                        else:
                            st.info("Consultez un médecin pour un avis professionnel.")
                            
                        if is_urgent:
                            st.error("⚠️ SITUATION CRITIQUE : CONTACTEZ LES SECOURS (15)")
                        
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
                st.markdown("""
                <div class='k-card' style='text-align:center;padding:60px 30px'>
                    <div style='font-size:4rem;opacity:.4;margin-bottom:16px'>🏥</div>
                    <p style='font-size:1.1rem;font-weight:600;margin-bottom:6px'>En attente de données...</p>
                    <p class='k-subtext' style='font-size:.85rem'>Veuillez remplir le formulaire à gauche.</p>
                </div>
                """, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    #  GESTION
    # ═══════════════════════════════════════════════════════════════
    elif page == "Gestion":
        st.markdown("## <span style='color:#00E5FF'>//</span> GESTION <span class='k-badge' style='vertical-align:middle;margin-left:8px'>ADMIN</span>", unsafe_allow_html=True)
        st.divider()
        
        st.markdown("#### 👥 Utilisateurs Enregistrés")
        df_u = pd.DataFrame([{"Login":k,"Nom":v["nom"],"Rôle":v["role"],"Modules":", ".join(v["acces"])} for k,v in USERS.items()])
        st.dataframe(df_u,use_container_width=True,hide_index=True)
        st.markdown("<br>",unsafe_allow_html=True)
        
        st.markdown("#### 🛡️ Logs de Sécurité Globaux")
        if st.session_state.historique:
            df_global = pd.DataFrame(st.session_state.historique[::-1])
            if "IP" in df_global.columns:
                df_global["IP"] = df_global["IP"].apply(mask_data)
            if "Utilisateur" in df_global.columns:
                df_global["Utilisateur"] = df_global["Utilisateur"].apply(mask_data)
                
            st.dataframe(df_global, use_container_width=True, hide_index=True)
            st.caption("🔒 Les IPs et identifiants sont masqués pour la confidentialité.")
        else:
            st.info("Aucun log disponible.")
            
        st.markdown("<div class='k-info'>Pour ajouter un utilisateur : ajouter une entrée dans USERS avec h() pour le mot de passe.<br><br>En production : utiliser PostgreSQL ou Firebase Auth.</div>",unsafe_allow_html=True)

# ── POINT D'ENTREE ────────────────────────────────────────────────
if not st.session_state.connecte:
    st.session_state.theme = st.sidebar.selectbox("Thème", ["Sombre", "Clair"], index=0 if st.session_state.theme == "Sombre" else 1)
    apply_theme()
    page_login()
else:
    app()