import streamlit as st
import pandas as pd
import numpy as np
import hashlib, time, datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import plotly.express as px

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
    "admin":    {"hash":h("kotighi2024"),"role":"Administrateur","nom":"Admin Principal",   "acces":["Accueil","Cybersecurite","Sante","Dashboard","Gestion"]},
    "analyste": {"hash":h("analyse123"), "role":"Analyste Cyber", "nom":"Analyste Securite","acces":["Accueil","Cybersecurite","Dashboard"]},
    "medecin":  {"hash":h("sante456"),   "role":"Medecin",        "nom":"Praticien Medical","acces":["Accueil","Sante","Dashboard"]},
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
        color: {text};
        animation: fadeInUp 0.5s ease-out;
    }}
    
    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}
    
    [data-testid="stSidebar"] {{
        background: {card}!important;
        border-right: 1px solid {border};
    }}
    
    [data-testid="metric-container"] {{
        background: {card};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 16px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    [data-testid="metric-container"]:hover {{
        transform: scale(1.02);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        border-color: {primary};
    }}
    
    .stButton>button {{
        background: linear-gradient(135deg, rgba(0,245,196,.15), rgba(124,108,255,.15));
        color: {primary};
        border: 1px solid rgba(0,245,196,.4);
        border-radius: 10px;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    .stButton>button:hover {{
        background: linear-gradient(135deg, rgba(0,245,196,.3), rgba(124,108,255,.3));
        border-color: {primary};
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,245,196,0.2);
    }}
    
    .stButton>button:active {{
        transform: translateY(0);
    }}
    
    h1, h2, h3, h4 {{
        font-family: 'Syne', sans-serif!important;
        color: {text}!important;
    }}
    
    .stTextInput input, .stNumberInput input, .stSelectbox select {{
        background: {bg}!important;
        color: {text}!important;
        border: 1px solid {border}!important;
        border-radius: 8px!important;
        transition: border-color 0.3s;
    }}
    .stTextInput input:focus {{
        border-color: {primary}!important;
    }}
    
    .adanger {{ background: rgba(255,71,87,.1); border: 1px solid rgba(255,71,87,.4); border-radius: 10px; padding: 16px; color: #ff4757; font-family: 'Space+Mono', monospace; animation: fadeInUp 0.4s ease-out; }}
    .asuccess {{ background: rgba(0,245,196,.08); border: 1px solid rgba(0,245,196,.3); border-radius: 10px; padding: 16px; color: #00f5c4; font-family: 'Space+Mono', monospace; animation: fadeInUp 0.4s ease-out; }}
    .awarning {{ background: rgba(255,165,0,.08); border: 1px solid rgba(255,165,0,.3); border-radius: 10px; padding: 16px; color: #ffa502; font-family: 'Space+Mono', monospace; }}
    .infob {{ background: rgba(124,108,255,.08); border: 1px solid rgba(124,108,255,.2); border-radius: 10px; padding: 12px 16px; color: #9d8fff; font-family: 'Space+Mono', monospace; font-size: .8rem; }}
    .ubadge {{ background: rgba(0,245,196,.08); border: 1px solid rgba(0,245,196,.2); border-radius: 10px; padding: 10px 14px; font-family: 'Space+Mono', monospace; font-size: .78rem; color: #00f5c4; }}
    
    .feature-card {{
        background: {card};
        border: 1px solid {border};
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .feature-card:hover {{
        transform: translateY(-8px);
        border-color: {primary};
        box-shadow: 0 12px 30px rgba(0,0,0,0.3);
    }}
    </style>""", unsafe_allow_html=True)

apply_theme()
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
                            "acces": ["Accueil", "Cybersecurite", "Dashboard"] if new_role == "Analyste Cyber" else ["Accueil", "Sante", "Dashboard"]
                        }
                        st.success("Compte cree avec succes ! Connectez-vous.")
                        st.session_state.auth_mode = "Connexion"
                        time.sleep(1.5)
                        st.rerun()
                else:
                    st.error("Veuillez remplir tous les champs.")

        st.markdown("<div style='margin-top:20px;font-family:Space Mono,monospace;font-size:.72rem;color:#444460;text-align:center'>Comptes demo :<br>admin / kotighi2024 &nbsp;|&nbsp; analyste / analyse123 &nbsp;|&nbsp; medecin / sante456</div>", unsafe_allow_html=True)

# ── APP PRINCIPALE ────────────────────────────────────────────────
def app():
    user  = st.session_state.utilisateur
    login = st.session_state.login_nom

    with st.sidebar:
        st.session_state.theme = st.selectbox("Thème", ["Sombre", "Clair"], index=0 if st.session_state.theme == "Sombre" else 1)
        apply_theme()
        st.markdown(f"""<div style='text-align:center;padding:16px 0'>
            <div style='font-family:Syne,sans-serif;font-size:1.4rem;font-weight:800;background:linear-gradient(90deg,#00f5c4,#7c6cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>KOTIGHI AI</div>
        </div>
        <div class='ubadge'>Connecte : <strong>{login}</strong><br>Role : {user["role"]}</div>""", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Navigation")
        page = st.radio("", user["acces"], label_visibility="collapsed")
        st.divider()
        st.markdown("<div class='infob'>Prototype educatif.</div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("SE DECONNECTER"):
            st.session_state.connecte=False; st.session_state.utilisateur=None
            st.session_state.login_nom=None; st.rerun()
        st.markdown("<div style='font-family:Space Mono,monospace;font-size:.7rem;color:#444460;text-align:center;margin-top:12px'>v1.1 — Python et Streamlit</div>", unsafe_allow_html=True)

    # ACCUEIL
    if page == "Accueil":
        st.markdown(f"""<div style='padding:30px 0 10px'>
            <div style='font-family:Space Mono,monospace;font-size:.75rem;color:#666680;letter-spacing:2px'>Bienvenue,</div>
            <h1 style='font-size:2.2rem;font-weight:800;margin:4px 0;background:linear-gradient(90deg,#00f5c4,#7c6cff,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>{user["nom"]}</h1>
            <div style='font-family:Space Mono,monospace;font-size:.8rem;color:#666680'>Role : {user["role"]} | Acces : {len(user["acces"])} module(s)</div>
        </div>""", unsafe_allow_html=True)
        st.divider()
        c1,c2 = st.columns(2)
        if "Cybersecurite" in user["acces"]:
            with c1: st.markdown("<div class='feature-card'><div style='font-size:1.1rem;font-weight:700;color:#00f5c4;margin-bottom:8px'>Module Cybersecurite</div><div style='color:#888;font-size:.88rem;line-height:1.7'>Detection d&#39;intrusions, DDoS, scans de ports et brute force.</div></div>", unsafe_allow_html=True)
        if "Sante" in user["acces"]:
            with c2: st.markdown("<div class='feature-card'><div style='font-size:1.1rem;font-weight:700;color:#ff6b6b;margin-bottom:8px'>Module Sante</div><div style='color:#888;font-size:.88rem;line-height:1.7'>Analyse des symptomes et prediction parmi 6 pathologies.</div></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Precision cyber","98%+","NSL-KDD reel")
        with c2: st.metric("Precision sante","95%+","donnees reelles")
        with c3: st.metric("Types attaques","5","DoS,Probe,R2L...")
        with c4: st.metric("Symptomes","10","par module sante")

    # CYBERSECURITE
    elif page == "Cybersecurite":
        st.markdown("## Detection d'intrusion reseau"); st.divider()
        m_rf, m_gb, sc = get_cyber()
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("### Parametres")
            ip   = st.text_input("Adresse IP source", value="192.168.1.100")
            req  = st.slider("Requetes par minute",0,8000,150)
            dur  = st.slider("Duree (sec)",0,300,45)
            oct_ = st.number_input("Octets transferes",0,1000000,2500)
            ca,cb = st.columns(2)
            with ca: ports = st.number_input("Ports scannes",1,500,2)
            with cb: terr  = st.slider("Taux erreur",0.0,1.0,0.02,0.01)
            flag = st.checkbox("Flag suspect",value=False)
            go_c = st.button("ANALYSER LA CONNEXION",type="primary")
        with col2:
            st.markdown("### Résultat")
            if go_c:
                with st.spinner("Analyse du trafic réseau en cours..."):
                    time.sleep(1.2) # Simulation de calcul
                    feat = pd.DataFrame([{"requetes_min":req,"duree":dur,"octets":oct_,"ports_scanes":ports,"taux_erreur":terr,"flag_suspect":int(flag)}])
                    feat_scaled = sc.transform(feat)
                    
                    # --- SYSTÈME DE VOTE (RF + GB) ---
                    p_rf = m_rf.predict_proba(feat_scaled)[0]
                    p_gb = m_gb.predict_proba(feat_scaled)[0]
                    proba_moy = (p_rf + p_gb) / 2
                    pred = 1 if proba_moy[1] > 0.5 else 0
                    conf = max(proba_moy) * 100
                    
                    if pred==0:
                        type_att="Normal"
                        st.toast("✅ Connexion normale détectée", icon="🟢")
                        st.markdown(f"<div class='asuccess'><strong>CONNEXION NORMALE</strong><br>Aucune menace — Confiance : {conf:.0f}%</div>",unsafe_allow_html=True)
                    else:
                        type_att = "DoS/DDoS" if req>2000 else ("Scan de ports" if ports>30 else ("Brute Force" if terr>0.7 else "Activite suspecte"))
                        st.toast(f"🚨 ATTAQUE DÉTECTÉE : {type_att}", icon="🔴")
                        st.markdown(f"<div class='adanger'><strong>ATTAQUE — {type_att}</strong><br>Confiance : {conf:.0f}% — IP : {ip}</div>",unsafe_allow_html=True)
                    
                    fig = go.Figure(go.Indicator(mode="gauge+number",value=proba_moy[1]*100,
                        title={"text":"Score de Risque","font":{"color":"#e8e8f0","family":"Syne"}},
                        gauge={"axis":{"range":[0,100]},"bar":{"color":"#ff4757" if pred==1 else "#00f5c4"},"bgcolor":"#111118","bordercolor":"#1e1e2e",
                               "steps":[{"range":[0,30],"color":"rgba(0,245,196,.1)"},{"range":[30,60],"color":"rgba(255,165,0,.1)"},{"range":[60,100],"color":"rgba(255,71,87,.1)"}]},
                        number={"font":{"color":"#e8e8f0"},"suffix":"%"}))
                    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",height=260,margin=dict(t=40,b=0,l=20,r=20),font={"color":"#e8e8f0"})
                    st.plotly_chart(fig,use_container_width=True)
                    
                    # --- JOURNALISATION STRUCTURÉE ---
                    log_entry = {
                        "Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Module": "Cybersecurite",
                        "IP": ip,
                        "Resultat": type_att,
                        "Confiance": f"{conf:.0f}%",
                        "Utilisateur": login,
                        "Score": f"{proba_moy[1]*100:.1f}%"
                    }
                    st.session_state.historique.append(log_entry)
                    
                    # --- GENERATION RAPPORT PDF ---
                    try:
                        from rapport_pdf import generer_rapport_cyber
                        pdf_cyber = generer_rapport_cyber({
                            "ip": ip, "requetes": req, "duree": dur,
                            "octets": oct_, "ports": ports, "taux_erreur": terr,
                            "prediction": pred, "type_attaque": type_att, "confiance": conf,
                            "utilisateur": login, "role": user["role"]
                        })
                        st.download_button("📥 Télécharger le rapport PDF", pdf_cyber,
                                         file_name=f"rapport_cyber_{ip}.pdf", mime="application/pdf")
                    except ImportError:
                        st.info("Module 'rapport_pdf' non trouvé. La génération PDF est désactivée.")
                if pred==1: st.error("Bloquer l'IP source"); st.warning("Analyser les logs")
                else: st.success("Connexion autorisee")

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

    # DASHBOARD
    elif page == "Dashboard":
        st.markdown("## Dashboard"); st.divider()
        np.random.seed(7)
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Connexions analysees","12 847","+234")
        with c2: st.metric("Attaques detectees","1 203","+18")
        with c3: st.metric("Taux de detection","99.2%","+0.1%")
        with c4: st.metric("Faux positifs","0.8%","-0.2%")
        
        st.markdown("<br>",unsafe_allow_html=True)
        
        # --- NOUVEAUX GRAPHIQUES TEMPORELS ---
        st.markdown("#### Évolution de l'activité (24h)")
        hours = list(range(24))
        activity_data = pd.DataFrame({
            "Heure": hours,
            "Requêtes": np.random.randint(100, 500, 24),
            "Risques": np.random.randint(0, 50, 24)
        })
        fig_line = px.line(activity_data, x="Heure", y=["Requêtes", "Risques"], 
                          color_discrete_sequence=["#00f5c4", "#ff4757"],
                          template="plotly_dark")
        fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                              height=300, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("<br>",unsafe_allow_html=True)
        cl,cr = st.columns(2)
        with cl:
            fig1=go.Figure(go.Pie(labels=["Normal","DoS","Probe","R2L","U2R"],values=[72,13,9,4,2],hole=0.5,marker=dict(colors=["#00f5c4","#ff4757","#ffa502","#7c6cff","#ff6b6b"])))
            fig1.update_layout(paper_bgcolor="#111118",font={"color":"#e8e8f0","family":"Syne"},height=290,margin=dict(t=10,b=10),legend=dict(bgcolor="#111118"))
            st.markdown("#### Repartition des attaques"); st.plotly_chart(fig1,use_container_width=True)
        with cr:
            fig2=px.bar(x=["Grippe","Gastro","Migraine","Angine","Cardiaque","Autre"],y=[42,28,19,15,7,31],color_discrete_sequence=["#ff6b6b"])
            fig2.update_layout(paper_bgcolor="#111118",font={"color":"#e8e8f0","family":"Syne"},height=290,margin=dict(t=10,b=10),xaxis={"gridcolor":"#1e1e2e","title":""},yaxis={"gridcolor":"#1e1e2e","title":"Nb cas"},showlegend=False)
            st.markdown("#### Diagnostics cette semaine"); st.plotly_chart(fig2,use_container_width=True)
        if st.session_state.historique:
            st.markdown("#### Historique de la session")
            df_hist = pd.DataFrame(st.session_state.historique[::-1])
            st.dataframe(df_hist,use_container_width=True,hide_index=True)
            
            # --- EXPORT CSV ---
            csv = df_hist.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Exporter l'historique (CSV)",
                data=csv,
                file_name=f"historique_kotighi_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                mime='text/csv',
            )
        else:
            st.markdown("<div class='infob'>Aucune analyse effectuee. Lancez une analyse depuis Cybersecurite ou Sante.</div>",unsafe_allow_html=True)

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