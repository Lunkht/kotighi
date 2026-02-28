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
DB_URL = st.secrets.get("postgres", {}).get("url", "postgresql://user:pass@localhost:5432/kotighi_db")

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
def apply_theme():
    is_dark = st.session_state.theme == "Sombre"
    bg = "#0a0a0f" if is_dark else "#f8f9fa"
    text = "#e8e8f0" if is_dark else "#212529"
    card = "#111118" if is_dark else "#ffffff"
    border = "#1e1e2e" if is_dark else "#dee2e6"
    subtext = "#666680" if is_dark else "#6c757d"
    primary = "#00f5c4"
    accent = "#7c6cff"

    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Syne:wght@700;800&family=Space+Mono&display=swap');
    
    @keyframes fadeInUp {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .stApp {{
        background: {bg};
        background-image: radial-gradient(circle at 10% 20%, rgba(124,108,255,0.05) 0%, transparent 20%),
                          radial-gradient(circle at 90% 80%, rgba(0,245,196,0.05) 0%, transparent 20%);
        color: {text};
        animation: fadeInUp 0.5s ease-out;
    }}
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    /* SIDEBAR GLASSMORPHISM */
    [data-testid="stSidebar"] {{
        background: {card}!important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-right: 1px solid {border};
    }}
    
    /* CARDS GLASSMORPHISM */
    [data-testid="metric-container"], .feature-card {{
        background: {card}cc; /* Opacité légère */
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        border: 1px solid {border};
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    [data-testid="metric-container"]:hover, .feature-card:hover {{
        transform: translateY(-5px) scale(1.01);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        border-color: {primary};
        background: {card}ee;
    }}
    
    /* INPUTS & WIDGETS */
    .stTextInput input, .stNumberInput input, .stSelectbox select, .stSlider {{
        background: {bg}88!important;
        backdrop-filter: blur(4px);
        color: {text}!important;
        border: 1px solid {border}!important;
        border-radius: 12px!important;
        transition: all 0.3s ease;
        padding: 10px 14px!important;
    }}
    .stTextInput input:focus, .stNumberInput input:focus, .stSelectbox select:focus {{
        border-color: {primary}!important;
        box-shadow: 0 0 0 2px {primary}33;
    }}
    
    /* BUTTONS NEO-FUTURISTIC */
    .stButton>button {{
        background: linear-gradient(135deg, rgba(0,245,196,.1), rgba(124,108,255,.1));
        color: {primary};
        border: 1px solid {primary}40;
        border-radius: 12px;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        letter-spacing: 0.5px;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        position: relative;
        overflow: hidden;
    }}
    
    .stButton>button:hover {{
        background: linear-gradient(135deg, {primary}20, {accent}20);
        border-color: {primary};
        color: {text};
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -5px {primary}40;
    }}
    
    .stButton>button:active {{
        transform: translateY(0);
        box-shadow: none;
    }}
    
    /* TYPOGRAPHY */
    h1 {{
        background: linear-gradient(90deg, {primary}, {accent});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem!important;
        letter-spacing: -1px;
        text-shadow: 0 10px 30px {primary}30;
    }}
    
    h2, h3, h4 {{
        font-family: 'Syne', sans-serif!important;
        color: {text}!important;
        letter-spacing: -0.5px;
    }}
    
    /* ALERTS & BADGES */
    .adanger {{ background: rgba(255,71,87,.1); border-left: 4px solid #ff4757; border-radius: 8px; padding: 16px; color: #ff4757; font-family: 'Space+Mono', monospace; animation: fadeInUp 0.4s ease-out; }}
    .asuccess {{ background: rgba(0,245,196,.08); border-left: 4px solid #00f5c4; border-radius: 8px; padding: 16px; color: #00f5c4; font-family: 'Space+Mono', monospace; animation: fadeInUp 0.4s ease-out; }}
    .awarning {{ background: rgba(255,165,0,.08); border-left: 4px solid #ffa502; border-radius: 8px; padding: 16px; color: #ffa502; font-family: 'Space+Mono', monospace; }}
    .infob {{ background: rgba(124,108,255,.08); border: 1px solid rgba(124,108,255,.2); border-radius: 12px; padding: 14px 18px; color: #9d8fff; font-family: 'Space+Mono', monospace; font-size: .85rem; line-height: 1.6; }}
    .ubadge {{ background: {bg}; border: 1px solid {primary}40; border-radius: 20px; padding: 6px 14px; font-family: 'Space+Mono', monospace; font-size: .75rem; color: {primary}; display: inline-block; margin-bottom: 8px; }}
    
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
    
    mode = st.radio("Action", ["Connexion", "Inscription"], 
                    index=0 if st.session_state.auth_mode == "Connexion" else 1,
                    horizontal=True, label_visibility="collapsed", key="auth_mode_selector")
    st.session_state.auth_mode = mode
    
    st.markdown(f"""<div style='text-align:center;padding:20px 0 10px'>
        <div style='font-family:Syne,sans-serif;font-size:2.5rem;font-weight:800;background:linear-gradient(90deg,#00f5c4,#7c6cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>KOTIGHI AI</div>
        <div style='font-family:Space Mono,monospace;font-size:.75rem;color:#666680;letter-spacing:3px;margin-top:6px'>{st.session_state.auth_mode.upper()}</div>
    </div>""", unsafe_allow_html=True)
    
    _,col,_ = st.columns([1,1.2,1])
    with col:
        if st.session_state.auth_mode == "Connexion":
            st.markdown("""<div style='background:#111118;border:1px solid #1e1e2e;border-radius:20px;padding:36px 32px;margin-top:20px'>
                <div style='font-size:1.1rem;font-weight:700;margin-bottom:4px'>Connexion</div>
                <div style='font-family:Space Mono,monospace;font-size:.75rem;color:#666680;margin-bottom:24px'>Identifiez-vous pour acceder a la plateforme</div>
            </div>""", unsafe_allow_html=True)
            if st.session_state.tentatives >= 5:
                st.markdown("<div class='adanger'>Trop de tentatives. Compte bloque.</div>", unsafe_allow_html=True)
                return
            login    = st.text_input("Identifiant", placeholder="Votre login")
            password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
            
            if st.button("SE CONNECTER", type="primary"):
                user = verifier(login, password)
                if user:
                    if user["role"] in ["Administrateur", "Analyste Cyber"]:
                        st.session_state.auth_2fa_pending = True
                        st.session_state.auth_user_temp = user
                        st.session_state.auth_login_temp = login.lower()
                        st.rerun()
                    else:
                        st.session_state.connecte = True
                        st.session_state.utilisateur = user
                        st.session_state.login_nom = login.lower()
                        st.session_state.tentatives = 0
                        st.success("Connexion reussie."); time.sleep(0.8); st.rerun()
                else:
                    st.session_state.tentatives += 1
                    st.markdown("<div class='adanger'>Identifiant ou mot de passe incorrect.</div>", unsafe_allow_html=True)
        
        elif st.session_state.get("auth_2fa_pending", False):
            st.markdown("""<div style='background:#111118;border:1px solid #1e1e2e;border-radius:20px;padding:36px 32px;margin-top:20px'>
                <div style='font-size:1.1rem;font-weight:700;margin-bottom:4px'>🔐 Vérification 2FA</div>
                <div style='font-family:Space Mono,monospace;font-size:.75rem;color:#666680;margin-bottom:24px'>Code envoyé à votre terminal sécurisé</div>
            </div>""", unsafe_allow_html=True)
            
            code = st.text_input("Code de sécurité (Simulation: 123456)", max_chars=6, type="password")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Valider Code", type="primary"):
                    if code == "123456":
                        st.session_state.connecte = True
                        st.session_state.utilisateur = st.session_state.auth_user_temp
                        st.session_state.login_nom = st.session_state.auth_login_temp
                        st.session_state.tentatives = 0
                        del st.session_state.auth_2fa_pending
                        st.success("Authentification forte réussie."); time.sleep(0.8); st.rerun()
                    else:
                        st.error("Code incorrect.")
            with c2:
                if st.button("Annuler"):
                    del st.session_state.auth_2fa_pending
                    st.rerun()
        
        else:
            st.markdown("""<div style='background:#111118;border:1px solid #1e1e2e;border-radius:20px;padding:36px 32px;margin-top:20px'>
                <div style='font-size:1.1rem;font-weight:700;margin-bottom:4px'>Inscription</div>
                <div style='font-family:Space Mono,monospace;font-size:.75rem;color:#666680;margin-bottom:24px'>Creez votre compte personnel</div>
            </div>""", unsafe_allow_html=True)
            new_login = st.text_input("Nouvel Identifiant")
            new_name  = st.text_input("Nom Complet")
            new_role  = st.selectbox("Role", ["Analyste Cyber", "Medecin"])
            new_pass  = st.text_input("Nouveau Mot de passe", type="password")
            if st.button("CREER MON COMPTE", type="primary"):
                if new_login and new_pass and new_name:
                    is_strong, msg_strong = check_password_strength(new_pass)
                    if not is_strong:
                        st.markdown(f"<div class='adanger'>{msg_strong}</div>", unsafe_allow_html=True)
                    else:
                        # Ici on ajouterait à PostgreSQL en temps normal
                        USERS[new_login.lower()] = {
                            "hash": h(new_pass),
                            "role": new_role,
                            "nom": new_name,
                            "acces": ["Dashboard", "Cybersecurite"] if new_role == "Analyste Cyber" else ["Dashboard", "Sante"]
                        }
                        st.success("Compte cree avec succes ! Connectez-vous.")
                        st.session_state.auth_mode = "Connexion"
                        time.sleep(1.5)
                        st.rerun()
                else:
                    st.error("Veuillez remplir tous les champs.")

        st.markdown("<div style='margin-top:20px;font-family:Space Mono,monospace;font-size:.72rem;color:#444460;text-align:center'>Comptes demo :<br>admin / kotighi2024 &nbsp;|&nbsp; analyste / analyse123 &nbsp;|&nbsp; medecin / sante456</div>", unsafe_allow_html=True)

# ── APPLICATION PRINCIPALE ────────────────────────────────────────
def app():
    # SIDEBAR
    with st.sidebar:
        st.session_state.theme = st.selectbox("Thème", ["Sombre", "Clair"], index=0 if st.session_state.theme == "Sombre" else 1)
        apply_theme()
        st.markdown(f"""<div style='text-align:center;padding:16px 0'>
            <div style='font-family:Syne,sans-serif;font-size:1.8rem;font-weight:800;background:linear-gradient(90deg,#00f5c4,#7c6cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>KOTIGHI AI</div>
            <div style='font-family:Space Mono,monospace;font-size:.65rem;color:#666680;letter-spacing:2px;margin-top:4px'>V2.0 • ULTIMATE EDITION</div>
        </div>""", unsafe_allow_html=True)
        
        # User Profile Card in Sidebar
        user = st.session_state.utilisateur
        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.05);padding:12px;border-radius:12px;margin-bottom:20px;border:1px solid rgba(255,255,255,0.1)'>
            <div style='font-size:0.8rem;color:#888'>Connecté en tant que</div>
            <div style='font-weight:bold;color:#fff;font-size:0.95rem'>👤 {user['nom']}</div>
            <div style='font-size:0.75rem;color:#00f5c4;margin-top:4px;text-transform:uppercase;letter-spacing:1px'>{user['role']}</div>
        </div>
        """, unsafe_allow_html=True)

        pages = [p for p in user["acces"] if p in ["Dashboard", "Cybersecurite", "Sante", "Gestion"]]
        page = st.radio("Navigation", pages, label_visibility="collapsed")
        
        st.markdown("---")
        if st.button("Se déconnecter"):
            st.session_state.connecte = False
            st.rerun()

    # DASHBOARD UNIFIÉ (ACCUEIL + STATS)
    if page == "Dashboard":
        # HERO SECTION RÉDUITE
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"""
            <div style='margin-top: 0px;'>
                <div class='ubadge'>TABLEAU DE BORD CENTRALISÉ</div>
                <h1 style='font-size:2rem!important'>Bienvenue, {user['nom']}</h1>
                <p style='font-size: 1rem; color: #888; line-height: 1.4; margin-bottom: 20px;'>
                    Surveillance active des systèmes et état de santé global.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            if lottie_scan:
                st_lottie(lottie_scan, height=150, key="hero_anim_mini")

        st.divider()

        # METRIQUES CLÉS
        np.random.seed(int(time.time()))
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Connexions analysées","12 847","+234")
        with c2: st.metric("Attaques bloquées","1 203","+18")
        with c3: st.metric("Diagnostics santé","452","+12")
        with c4: st.metric("Fiabilité IA","99.2%","+0.1%")
        
        st.markdown("<br>",unsafe_allow_html=True)
        
        # GRAPHIQUES ET ACCÈS RAPIDE
        cl,cr = st.columns([2, 1])
        
        with cl:
            st.markdown("#### 📈 Activité Temps Réel (24h)")
            hours = list(range(24))
            activity_data = pd.DataFrame({
                "Heure": hours,
                "Requêtes": np.random.randint(100, 500, 24),
                "Menaces": np.random.randint(0, 50, 24)
            })
            fig_line = px.line(activity_data, x="Heure", y=["Requêtes", "Menaces"], 
                              color_discrete_sequence=["#00f5c4", "#ff4757"],
                              template="plotly_dark")
            fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                                  height=320, margin=dict(t=20, b=20, l=20, r=20),
                                  legend=dict(orientation="h", y=1.1))
            st.plotly_chart(fig_line, use_container_width=True)

        with cr:
            st.markdown("#### 🚀 Accès Rapide")
            if "Cybersecurite" in user["acces"]:
                st.markdown("""
                <div class='feature-card' style='margin-bottom:15px;padding:15px'>
                    <div style='font-weight:700;color:#00f5c4;margin-bottom:5px'>🛡️ Module Cyber</div>
                    <div style='font-size:0.8rem;color:#888'>Lancer un scan réseau</div>
                </div>
                """, unsafe_allow_html=True)
            
            if "Sante" in user["acces"]:
                st.markdown("""
                <div class='feature-card' style='padding:15px'>
                    <div style='font-weight:700;color:#ff6b6b;margin-bottom:5px'>🩺 Module Santé</div>
                    <div style='font-size:0.8rem;color:#888'>Nouveau diagnostic</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>",unsafe_allow_html=True)
        
        # HISTORIQUE RÉCENT (Aperçu)
        st.markdown("#### 🕒 Dernières Activités")
        if st.session_state.historique:
            df_hist = pd.DataFrame(st.session_state.historique[::-1]).head(5)
            st.dataframe(df_hist,use_container_width=True,hide_index=True)
        else:
            st.info("Aucune activité récente.")
    
    # CYBERSECURITE
    elif page == "Cybersecurite":
        # --- UI CONSOLE SOC ---
        st.markdown("""
        <style>
        .stApp { background: #000000; }
        .block-container { max-width: 95%!important; padding-top: 2rem; }
        h1, h2, h3 { font-family: 'Space Mono', monospace!important; text-transform: uppercase; letter-spacing: 2px; }
        .stTextInput input, .stTextArea textarea { 
            background: #0a0a0f!important; 
            border: 1px solid #333!important; 
            color: #00f5c4!important; 
            font-family: 'Space Mono', monospace!important;
        }
        .soc-panel {
            border: 1px solid #1e1e2e;
            background: #050508;
            padding: 15px;
            margin-bottom: 15px;
        }
        .soc-header {
            color: #666;
            font-size: 0.75rem;
            text-transform: uppercase;
            border-bottom: 1px solid #1e1e2e;
            padding-bottom: 5px;
            margin-bottom: 10px;
            font-family: 'Space Mono', monospace;
        }
        .status-dot {
            height: 8px; width: 8px; border-radius: 50%; display: inline-block; margin-right: 5px;
        }
        .dot-green { background: #00f5c4; box-shadow: 0 0 5px #00f5c4; }
        .dot-red { background: #ff4757; box-shadow: 0 0 5px #ff4757; animation: blink 1s infinite; }
        @keyframes blink { 50% { opacity: 0.5; } }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("## <span style='color:#00f5c4'>//</span> SOC TERMINAL <span style='font-size:0.8rem;color:#666'>v3.0.1-BETA</span>", unsafe_allow_html=True)
        
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
                        with cols[3]: st.markdown(f"<span style='color:{'#ff4757' if is_threat else '#00f5c4'}'>{status_txt}</span>", unsafe_allow_html=True)
                        with cols[4]: 
                            if st.button("STOP", key=f"del_{target['ip']}"):
                                st.session_state.watchlist.remove(target)
                                st.rerun()
                        st.markdown("<div style='border-bottom:1px solid #1e1e2e;margin:5px 0'></div>", unsafe_allow_html=True)
                        
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
                st.markdown(f"<div style='font-family:monospace;font-size:0.7rem;color:#00f5c4;margin-bottom:4px'>{evt}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='soc-panel'>", unsafe_allow_html=True)
            st.markdown("<div class='soc-header'>ÉTAT SYSTÈME</div>", unsafe_allow_html=True)
            st.progress(88, text="CPU LOAD")
            st.progress(45, text="RAM USAGE")
            st.progress(12, text="NETWORK I/O")
            st.markdown("</div>", unsafe_allow_html=True)

    # SANTE
    elif page == "Sante":
        st.markdown("## Analyse de symptomes")
        st.markdown("<div class='awarning'>Outil educatif. Consultez un medecin.</div>",unsafe_allow_html=True)
        st.divider()
        ms,labels,conseils_prev = get_sante()
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("### Symptômes du patient")
            age   = st.number_input("Age",1,120,35)
            dur_s = st.selectbox("Duree",["Moins de 24h","1 a 3 jours","3 a 7 jours","Plus d'une semaine"])
            
            # --- REGROUPEMENT LOGIQUE DES SYMPTÔMES ---
            with st.expander("Général & Douleurs", expanded=True):
                c1, c2 = st.columns(2)
                with c1: fievre=st.checkbox("🌡️ Fièvre"); fat=st.checkbox("😴 Fatigue"); fri=st.checkbox("🥶 Frissons")
                with c2: mus=st.checkbox("💪 Musculaire"); tete=st.checkbox("🤕 Maux de tête"); ver=st.checkbox("� Vertiges")
            
            with st.expander("Respiratoire & ORL", expanded=True):
                c1, c2 = st.columns(2)
                with c1: toux=st.checkbox("� Toux"); ess=st.checkbox("😮 Essoufflement"); odo=st.checkbox("� Perte odorat")
                with c2: gorge=st.checkbox("😮‍💨 Gorge"); thor=st.checkbox("� Thorax"); pal=st.checkbox("💓 Palpitations")
                
            with st.expander("Digestif", expanded=True):
                c1, c2 = st.columns(2)
                with c1: nau=st.checkbox("🤢 Nausées")
                with c2: diar=st.checkbox("� Diarrhée")
            
            go_s = st.button("ANALYSER LES SYMPTÔMES",type="primary")
        with col2:
            st.markdown("### Résultat")
            if go_s:
                nb = sum([fievre,toux,fat,tete,gorge,nau,thor,ess,diar,fri,odo,mus,pal,ver])
                if nb==0: st.warning("Sélectionnez au moins un symptôme.")
                else:
                    feat = pd.DataFrame([{"fievre":int(fievre),"toux":int(toux),"fatigue":int(fat),"maux_tete":int(tete),"douleur_gorge":int(gorge),"nausees":int(nau),"douleur_thorax":int(thor),"essoufflement":int(ess),"diarrhee":int(diar),"frissons":int(fri),"perte_odorat":int(odo),"douleurs_musculaires":int(mus),"palpitations":int(pal),"vertiges":int(ver)}])
                    pred=ms.predict(feat)[0]; proba=ms.predict_proba(feat)[0]
                    diag=labels[pred]; conf=proba[pred]*100
                    urgent = "cardiaque" in diag.lower() or "covid" in diag.lower()
                    
                    if urgent: 
                        st.toast(f"🚨 ALERTE CRITIQUE : {diag}", icon="🚨")
                        st.markdown(f"<div class='adanger'><strong>CONSULTATION URGENTE</strong><br>Diagnostic : {diag}<br>Confiance : {conf:.0f}%</div>",unsafe_allow_html=True)
                    else: 
                        st.toast(f"🩺 Diagnostic : {diag}", icon="🩺")
                        st.markdown(f"<div class='asuccess'><strong>Diagnostic : {diag}</strong><br>Confiance : {conf:.0f}% — {nb} symptôme(s)</div>",unsafe_allow_html=True)
                    
                    # --- CONSEILS PERSONNALISÉS ---
                    st.markdown("#### 💡 Conseils & Prévention")
                    for conseil in conseils_prev.get(diag, []):
                        st.info(f"👉 {conseil}")
                    
                    # --- EXPLICATION (SHAP SIMPLIFIÉ) ---
                    st.markdown("#### 🔍 Pourquoi ce diagnostic ?")
                    # Calcul simple d'importance basé sur les symptômes présents vs attendus pour ce diagnostic
                    top_facteurs = []
                    if "covid" in diag.lower() and odo: top_facteurs.append("Perte d'odorat (Spécifique)")
                    if "grippe" in diag.lower() and mus: top_facteurs.append("Douleurs musculaires (Typique)")
                    if "cardiaque" in diag.lower() and thor: top_facteurs.append("Douleur thoracique (Critique)")
                    if fievre: top_facteurs.append("Fièvre (Infection)")
                    
                    if top_facteurs:
                        st.markdown(f"Facteurs déterminants : **{', '.join(top_facteurs)}**")
                    else:
                        st.markdown("Combinaison globale des symptômes.")

                    df_p = pd.DataFrame({"Diagnostic":labels,"Probabilite":proba*100}).sort_values("Probabilite",ascending=True)
                    fig = px.bar(df_p,x="Probabilite",y="Diagnostic",orientation="h",color="Probabilite",color_continuous_scale=["#1e1e2e","#7c6cff","#ff6b6b"])
                    fig.update_layout(paper_bgcolor="#111118",height=290,margin=dict(t=10,b=10),font={"color":"#e8e8f0","family":"Syne"},showlegend=False,coloraxis_showscale=False,xaxis={"gridcolor":"#1e1e2e","title":"Probabilite (%)"},yaxis={"gridcolor":"#1e1e2e","title":""})
                    st.plotly_chart(fig,use_container_width=True)
                    # --- JOURNALISATION STRUCTURÉE ---
                    log_entry = {
                        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Module": "Sante",
                        "Resultat": diag,
                        "Confiance": f"{conf:.0f}%",
                        "Utilisateur": login,
                        "Detail": f"Age {age}, {nb} sympt."
                    }
                    st.session_state.historique.append(log_entry)
                    
                    # --- GENERATION RAPPORT PDF ---
                    try:
                        from rapport_pdf import generer_rapport_sante
                        ALL_SYM = ["fievre","toux","fatigue","maux_tete","douleur_gorge","nausees","douleur_thorax","essoufflement","diarrhee","frissons","perte_odorat","douleurs_musculaires","palpitations","vertiges"]
                        VAL_SYM = [fievre,toux,fat,tete,gorge,nau,thor,ess,diar,fri,odo,mus,pal,ver]
                        pdf_sante = generer_rapport_sante({
                            "age": age, "duree_symptomes": dur_s,
                            "symptomes": [s for s, v in zip(ALL_SYM, VAL_SYM) if v],
                            "diagnostic": diag, "confiance": conf, "urgent": urgent,
                            "utilisateur": login, "role": user["role"]
                        })
                        st.download_button("📥 Télécharger le rapport PDF", pdf_sante,
                                         file_name=f"rapport_sante_{login}.pdf", mime="application/pdf")
                    except ImportError:
                        st.info("Module 'rapport_pdf' non trouvé. La génération PDF est désactivée.")
                    if urgent: st.error("Appelez le 15 (SAMU)")
                    st.info("Restez hydrate"); st.warning("Consultez un medecin si aggravation")

    # GESTION
    elif page == "Gestion":
        st.markdown("## Gestion des utilisateurs"); st.divider()
        df_u = pd.DataFrame([{"Login":k,"Nom":v["nom"],"Role":v["role"],"Modules":", ".join(v["acces"])} for k,v in USERS.items()])
        st.dataframe(df_u,use_container_width=True,hide_index=True)
        st.markdown("<br>",unsafe_allow_html=True)
        
        # --- HISTORIQUE GLOBAL SÉCURISÉ ---
        st.markdown("### 🛡️ Logs de sécurité globaux")
        if st.session_state.historique:
            df_global = pd.DataFrame(st.session_state.historique[::-1])
            # Masquage des données sensibles pour l'affichage
            if "IP" in df_global.columns:
                df_global["IP"] = df_global["IP"].apply(mask_data)
            if "Utilisateur" in df_global.columns:
                df_global["Utilisateur"] = df_global["Utilisateur"].apply(mask_data)
                
            st.dataframe(df_global, use_container_width=True, hide_index=True)
            st.caption("🔒 Les IPs et identifiants sont masqués pour la confidentialité.")
        else:
            st.info("Aucun log disponible.")
            
        st.markdown("<div class='infob'>Pour ajouter un utilisateur : ajouter une entree dans USERS avec h() pour le mot de passe.<br><br>En production : utiliser PostgreSQL ou Firebase Auth.</div>",unsafe_allow_html=True)

# ── POINT D'ENTREE ────────────────────────────────────────────────
if not st.session_state.connecte:
    st.session_state.theme = st.sidebar.selectbox("Thème", ["Sombre", "Clair"], index=0 if st.session_state.theme == "Sombre" else 1)
    apply_theme()
    page_login()
else:
    app()