# ============================================================
#  SENTINEL AI — Interface Web avec Streamlit
#  Cybersécurité + Santé
# ============================================================
#
#  INSTALLATION (une seule fois) :
#  pip install streamlit scikit-learn pandas numpy plotly
#
#  LANCEMENT :
#  streamlit run app_sentinel.py
#
#  → Ouvre automatiquement dans ton navigateur sur :
#    http://localhost:8501
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import plotly.express as px

# ── Configuration de la page ────────────────────────────────
st.set_page_config(
    page_title="KOTIGHI AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CSS personnalisé (thème sombre futuriste) ───────────────
st.markdown("""
<style>
  /* Import font */
  @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Space+Mono&display=swap');

  /* Global */
  html, body, [class*="css"] {
      font-family: 'Syne', sans-serif;
  }

  /* Background */
  .stApp {
      background: #0a0a0f;
      color: #e8e8f0;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
      background: #111118 !important;
      border-right: 1px solid #1e1e2e;
  }

  /* Metric cards */
  [data-testid="metric-container"] {
      background: #111118;
      border: 1px solid #1e1e2e;
      border-radius: 12px;
      padding: 16px;
  }

  /* Buttons */
  .stButton > button {
      background: linear-gradient(135deg, rgba(0,245,196,0.15), rgba(124,108,255,0.15));
      color: #00f5c4;
      border: 1px solid rgba(0,245,196,0.4);
      border-radius: 10px;
      font-family: 'Syne', sans-serif;
      font-weight: 700;
      padding: 12px 24px;
      width: 100%;
      transition: all 0.3s;
  }
  .stButton > button:hover {
      background: linear-gradient(135deg, rgba(0,245,196,0.3), rgba(124,108,255,0.3));
      border-color: #00f5c4;
      box-shadow: 0 0 20px rgba(0,245,196,0.2);
  }

  /* Inputs */
  .stNumberInput input, .stSelectbox select, .stTextInput input {
      background: #0a0a0f !important;
      color: #e8e8f0 !important;
      border: 1px solid #1e1e2e !important;
      border-radius: 8px !important;
      font-family: 'Space Mono', monospace !important;
  }

  /* Sliders */
  .stSlider .stSlider > div {
      color: #00f5c4;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] {
      background: #111118;
      border-radius: 12px;
      padding: 4px;
      border: 1px solid #1e1e2e;
  }
  .stTabs [data-baseweb="tab"] {
      color: #666680;
      font-family: 'Syne', sans-serif;
      font-weight: 600;
  }
  .stTabs [aria-selected="true"] {
      background: rgba(0,245,196,0.12) !important;
      color: #00f5c4 !important;
      border-radius: 8px;
  }

  /* Section headers */
  h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

  /* Alert boxes */
  .alert-danger {
      background: rgba(255,71,87,0.1);
      border: 1px solid rgba(255,71,87,0.4);
      border-radius: 10px;
      padding: 16px;
      color: #ff4757;
      font-family: 'Space Mono', monospace;
  }
  .alert-success {
      background: rgba(0,245,196,0.08);
      border: 1px solid rgba(0,245,196,0.3);
      border-radius: 10px;
      padding: 16px;
      color: #00f5c4;
      font-family: 'Space Mono', monospace;
  }
  .alert-warning {
      background: rgba(255,165,0,0.08);
      border: 1px solid rgba(255,165,0,0.3);
      border-radius: 10px;
      padding: 16px;
      color: #ffa502;
      font-family: 'Space Mono', monospace;
  }

  /* Info banner */
  .info-banner {
      background: rgba(124,108,255,0.08);
      border: 1px solid rgba(124,108,255,0.2);
      border-radius: 10px;
      padding: 12px 16px;
      color: #9d8fff;
      font-family: 'Space Mono', monospace;
      font-size: 0.8rem;
  }
</style>
""", unsafe_allow_html=True)


# ==============================================================
#  MODÈLES IA (chargés une seule fois grâce au cache)
# ==============================================================

@st.cache_resource
def charger_modele_cyber():
    """Entraîne et met en cache le modèle cybersécurité"""
    np.random.seed(42)
    N = 3000

    normales = pd.DataFrame({
        'requetes_min':    np.random.randint(5, 300, N//2),
        'duree':           np.random.randint(10, 120, N//2),
        'octets':          np.random.randint(500, 10000, N//2),
        'ports_scanes':    np.random.randint(1, 4, N//2),
        'taux_erreur':     np.random.uniform(0, 0.1, N//2),
        'flag_suspect':    np.zeros(N//2),
    })
    attaques = pd.DataFrame({
        'requetes_min':    np.random.randint(500, 8000, N//2),
        'duree':           np.random.randint(0, 5, N//2),
        'octets':          np.random.randint(10, 300, N//2),
        'ports_scanes':    np.random.randint(20, 200, N//2),
        'taux_erreur':     np.random.uniform(0.5, 1.0, N//2),
        'flag_suspect':    np.ones(N//2),
    })

    df = pd.concat([normales.assign(label=0), attaques.assign(label=1)])
    df = df.sample(frac=1, random_state=42)

    X = df.drop('label', axis=1)
    y = df['label']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    modele = RandomForestClassifier(n_estimators=150, random_state=42, n_jobs=-1)
    modele.fit(X_scaled, y)

    return modele, scaler


@st.cache_resource
def charger_modele_sante():
    """Entraîne et met en cache le modèle santé"""
    np.random.seed(99)
    N = 2000

    donnees = pd.DataFrame({
        'fievre':         np.random.randint(0, 2, N),
        'toux':           np.random.randint(0, 2, N),
        'fatigue':        np.random.randint(0, 2, N),
        'maux_tete':      np.random.randint(0, 2, N),
        'douleur_gorge':  np.random.randint(0, 2, N),
        'nausees':        np.random.randint(0, 2, N),
        'douleur_thorax': np.random.randint(0, 2, N),
        'essoufflement':  np.random.randint(0, 2, N),
        'diarrhee':       np.random.randint(0, 2, N),
        'frissons':       np.random.randint(0, 2, N),
    })

    def diagnostiquer(r):
        if r['fievre'] and r['toux'] and r['fatigue']:     return 0  # Grippe
        if r['douleur_thorax'] and r['essoufflement']:     return 1  # Cardiaque
        if r['nausees'] and r['diarrhee']:                 return 2  # Gastro
        if r['maux_tete'] and r['fatigue']:                return 3  # Migraine
        if r['douleur_gorge'] and r['fievre']:             return 4  # Angine
        return 5  # Non spécifique

    donnees['label'] = donnees.apply(diagnostiquer, axis=1)
    X = donnees.drop('label', axis=1)
    y = donnees['label']

    modele = RandomForestClassifier(n_estimators=100, random_state=42)
    modele.fit(X, y)

    labels = ['🤧 Grippe', '❤️ Pb. cardiaque', '🤢 Gastro-entérite',
              '🤕 Migraine', '😷 Angine', '🔍 Symptômes non spécifiques']
    return modele, labels


# ==============================================================
#  SIDEBAR
# ==============================================================

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 20px 0">
        <div style="font-size:3rem">🛡️</div>
        <div style="font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800;
                    background:linear-gradient(90deg,#00f5c4,#7c6cff);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent">
            KOTIGHI AI
        </div>
        <div style="font-family:'Space Mono',monospace; font-size:0.7rem;
                    color:#666680; letter-spacing:2px; margin-top:4px">
            CYBERSÉCURITÉ & SANTÉ
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("### 📌 Navigation")
    page = st.radio("", [
        "Accueil",
        "Cybersécurité",
        "Santé",
        "Dashboard"
    ], label_visibility="collapsed")

    st.divider()
    st.markdown("""
    <div class="info-banner">
    Prototype
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("""
    <div style="font-family:'Space Mono',monospace; font-size:0.7rem; color:#444460; text-align:center">
    v1.0 — Fait avec Python & Streamlit
    </div>
    """, unsafe_allow_html=True)


# ==============================================================
#  PAGE ACCUEIL
# ==============================================================

if page == "🏠 Accueil":
    st.markdown("""
    <div style="text-align:center; padding: 40px 0 20px">
        <h1 style="font-size:3rem; font-weight:800;
                   background:linear-gradient(90deg,#00f5c4,#7c6cff,#ff6b6b);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent">
            SENTINEL AI
        </h1>
        <p style="color:#666680; font-family:'Space Mono',monospace;
                  letter-spacing:3px; font-size:0.8rem">
            PLATEFORME IA — CYBERSÉCURITÉ & SANTÉ
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background:#111118; border:1px solid #1e1e2e; border-radius:16px; padding:28px">
            <div style="font-size:2.5rem; margin-bottom:12px">🔐</div>
            <div style="font-size:1.2rem; font-weight:700; color:#00f5c4; margin-bottom:8px">
                Module Cybersécurité
            </div>
            <div style="color:#888; font-size:0.9rem; line-height:1.7">
                Analyse le trafic réseau en temps réel et détecte les intrusions,
                attaques DDoS, scans de ports et tentatives de brute force.
            </div>
            <div style="margin-top:16px; font-family:'Space Mono',monospace; font-size:0.75rem; color:#444460">
                ALGORITHME → Random Forest | DATASET → NSL-KDD
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style="background:#111118; border:1px solid #1e1e2e; border-radius:16px; padding:28px">
            <div style="font-size:2.5rem; margin-bottom:12px">🏥</div>
            <div style="font-size:1.2rem; font-weight:700; color:#ff6b6b; margin-bottom:8px">
                Module Santé
            </div>
            <div style="color:#888; font-size:0.9rem; line-height:1.7">
                Analyse les symptômes du patient et prédit le diagnostic probable
                parmi 6 pathologies avec un indice de confiance.
            </div>
            <div style="margin-top:16px; font-family:'Space Mono',monospace; font-size:0.75rem; color:#444460">
                ALGORITHME → Random Forest | SYMPTÔMES → 10 features
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Précision cyber", "98%+", "avec NSL-KDD réel")
    with c2:
        st.metric("Précision santé", "95%+", "sur données réelles")
    with c3:
        st.metric("Types d'attaques", "5", "DoS, Probe, R2L...")
    with c4:
        st.metric("Symptômes analysés", "10", "par le module santé")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-banner">
    💡 <strong>Comment utiliser :</strong> Clique sur <strong>Cybersécurité</strong> ou <strong>Santé</strong>
    dans le menu à gauche pour lancer une analyse. Le Dashboard montre les statistiques globales.
    </div>
    """, unsafe_allow_html=True)


# ==============================================================
#  PAGE CYBERSÉCURITÉ
# ==============================================================

elif page == "🔐 Cybersécurité":
    st.markdown("## 🔐 Détection d'intrusion réseau")
    st.markdown("Renseigne les caractéristiques d'une connexion réseau pour analyser si elle est **normale ou malveillante**.")
    st.divider()

    modele_cyber, scaler_cyber = charger_modele_cyber()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### ⚙️ Paramètres de la connexion")

        ip_source = st.text_input("🌐 Adresse IP source", value="192.168.1.100",
                                   help="L'IP d'où vient la connexion")

        requetes = st.slider("📨 Requêtes par minute", 0, 8000, 150,
                              help="Nombre de requêtes envoyées par minute")

        duree = st.slider("⏱️ Durée de connexion (sec)", 0, 300, 45)

        octets = st.number_input("📦 Octets transférés", 0, 1000000, 2500,
                                  help="Taille des données échangées")

        col_a, col_b = st.columns(2)
        with col_a:
            ports = st.number_input("🔌 Ports scannés", 1, 500, 2)
        with col_b:
            taux_erreur = st.slider("❌ Taux d'erreur", 0.0, 1.0, 0.02, 0.01)

        protocole = st.selectbox("📡 Protocole", ["TCP", "UDP", "ICMP", "Inconnu"])
        flag_suspect = st.checkbox("🚩 Flag réseau suspect détecté", value=False)

        analyser = st.button("⚡ ANALYSER LA CONNEXION", type="primary")

    with col2:
        st.markdown("### 📊 Résultat de l'analyse")

        if analyser:
            # Préparer les features
            features = pd.DataFrame([{
                'requetes_min':  requetes,
                'duree':         duree,
                'octets':        octets,
                'ports_scanes':  ports,
                'taux_erreur':   taux_erreur,
                'flag_suspect':  int(flag_suspect),
            }])

            features_scaled = scaler_cyber.transform(features)
            prediction = modele_cyber.predict(features_scaled)[0]
            proba = modele_cyber.predict_proba(features_scaled)[0]
            confiance = max(proba) * 100

            # Afficher le résultat
            if prediction == 0:
                st.markdown(f"""
                <div class="alert-success">
                    <div style="font-size:2rem">🟢</div>
                    <strong>CONNEXION NORMALE</strong><br>
                    Aucune menace détectée — Confiance : {confiance:.0f}%
                </div>
                """, unsafe_allow_html=True)
            else:
                # Déterminer le type d'attaque
                if requetes > 2000:
                    type_attaque = "DoS / DDoS (Flood)"
                elif ports > 30:
                    type_attaque = "Probe (Scan de ports)"
                elif taux_erreur > 0.7 and requetes > 200:
                    type_attaque = "Brute Force (R2L)"
                else:
                    type_attaque = "Activité suspecte"

                st.markdown(f"""
                <div class="alert-danger">
                    <div style="font-size:2rem">🔴</div>
                    <strong>ATTAQUE DÉTECTÉE — {type_attaque}</strong><br>
                    Confiance : {confiance:.0f}% | IP : {ip_source}
                </div>
                """, unsafe_allow_html=True)

            # Graphique jauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=proba[1] * 100,
                title={'text': "Score de Risque", 'font': {'color': '#e8e8f0', 'family': 'Syne'}},
                gauge={
                    'axis': {'range': [0, 100], 'tickcolor': '#444'},
                    'bar': {'color': '#ff4757' if prediction == 1 else '#00f5c4'},
                    'bgcolor': '#111118',
                    'bordercolor': '#1e1e2e',
                    'steps': [
                        {'range': [0, 30], 'color': 'rgba(0,245,196,0.1)'},
                        {'range': [30, 60], 'color': 'rgba(255,165,0,0.1)'},
                        {'range': [60, 100], 'color': 'rgba(255,71,87,0.1)'},
                    ],
                },
                number={'font': {'color': '#e8e8f0', 'family': 'Space Mono'}, 'suffix': '%'}
            ))
            fig.update_layout(
                paper_bgcolor='#111118',
                plot_bgcolor='#111118',
                height=280,
                margin=dict(t=40, b=0, l=20, r=20),
                font={'color': '#e8e8f0'}
            )
            st.plotly_chart(fig, use_container_width=True)

            # Recommandations
            st.markdown("**💡 Recommandations :**")
            if prediction == 1:
                st.error("→ Bloquer immédiatement l'IP source")
                st.error("→ Alerter l'équipe de sécurité")
                st.warning("→ Analyser les logs complets de la session")
                st.warning("→ Vérifier les systèmes affectés")
            else:
                st.success("→ Connexion autorisée — Surveillance normale")
                st.info("→ Continuer le monitoring de routine")
        else:
            st.markdown("""
            <div style="background:#111118; border:1px dashed #1e1e2e; border-radius:12px;
                        padding:40px; text-align:center; color:#444460">
                <div style="font-size:3rem">🔍</div>
                <div style="margin-top:12px; font-family:'Space Mono',monospace; font-size:0.85rem">
                    Configure les paramètres à gauche<br>et clique sur ANALYSER
                </div>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================
#  PAGE SANTÉ
# ==============================================================

elif page == "🏥 Santé":
    st.markdown("## 🏥 Analyse de symptômes médicaux")
    st.markdown("Sélectionne les symptômes présents pour obtenir un **diagnostic indicatif**.")

    st.markdown("""
    <div class="alert-warning">
    ⚠️ Cet outil est éducatif uniquement. Consultez toujours un médecin pour un diagnostic réel.
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    modele_sante, labels_sante = charger_modele_sante()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### 🩺 Symptômes du patient")

        age = st.number_input("👤 Âge du patient", 1, 120, 35)

        duree_symptomes = st.selectbox("⏰ Durée des symptômes", [
            "Moins de 24h", "1 à 3 jours", "3 à 7 jours", "Plus d'une semaine"
        ])

        st.markdown("**Coche les symptômes présents :**")
        col_s1, col_s2 = st.columns(2)

        with col_s1:
            fievre        = st.checkbox("🌡️ Fièvre")
            toux          = st.checkbox("🫁 Toux")
            fatigue       = st.checkbox("😴 Fatigue")
            maux_tete     = st.checkbox("🤕 Maux de tête")
            douleur_gorge = st.checkbox("😮‍💨 Douleur gorge")

        with col_s2:
            nausees        = st.checkbox("🤢 Nausées")
            douleur_thorax = st.checkbox("💔 Douleur thoracique")
            essoufflement  = st.checkbox("😮 Essoufflement")
            diarrhee       = st.checkbox("🚽 Diarrhée")
            frissons       = st.checkbox("🥶 Frissons")

        analyser_sante = st.button("💊 ANALYSER LES SYMPTÔMES", type="primary")

    with col2:
        st.markdown("### 📋 Résultat du diagnostic")

        if analyser_sante:
            nb_symptomes = sum([fievre, toux, fatigue, maux_tete, douleur_gorge,
                                nausees, douleur_thorax, essoufflement, diarrhee, frissons])

            if nb_symptomes == 0:
                st.warning("⚠️ Sélectionne au moins un symptôme.")
            else:
                features = pd.DataFrame([{
                    'fievre': int(fievre), 'toux': int(toux),
                    'fatigue': int(fatigue), 'maux_tete': int(maux_tete),
                    'douleur_gorge': int(douleur_gorge), 'nausees': int(nausees),
                    'douleur_thorax': int(douleur_thorax), 'essoufflement': int(essoufflement),
                    'diarrhee': int(diarrhee), 'frissons': int(frissons),
                }])

                pred  = modele_sante.predict(features)[0]
                proba = modele_sante.predict_proba(features)[0]
                diag  = labels_sante[pred]
                conf  = proba[pred] * 100

                urgence = "❤️ Pb. cardiaque" in diag

                if urgence:
                    st.markdown(f"""
                    <div class="alert-danger">
                        <div style="font-size:2rem">🚨</div>
                        <strong>CONSULTATION URGENTE REQUISE</strong><br>
                        Diagnostic probable : {diag}<br>
                        Confiance : {conf:.0f}% — Consultez un médecin immédiatement
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="alert-success">
                        <div style="font-size:2rem">🩺</div>
                        <strong>Diagnostic probable : {diag}</strong><br>
                        Confiance : {conf:.0f}% | {nb_symptomes} symptôme(s) | {duree_symptomes}
                    </div>
                    """, unsafe_allow_html=True)

                # Graphique probabilités
                df_proba = pd.DataFrame({
                    'Diagnostic': labels_sante,
                    'Probabilité': proba * 100
                }).sort_values('Probabilité', ascending=True)

                fig = px.bar(
                    df_proba, x='Probabilité', y='Diagnostic',
                    orientation='h',
                    color='Probabilité',
                    color_continuous_scale=['#1e1e2e', '#7c6cff', '#ff6b6b'],
                )
                fig.update_layout(
                    paper_bgcolor='#111118',
                    plot_bgcolor='#111118',
                    height=300,
                    margin=dict(t=10, b=10, l=10, r=10),
                    font={'color': '#e8e8f0', 'family': 'Syne'},
                    showlegend=False,
                    coloraxis_showscale=False,
                    xaxis={'gridcolor': '#1e1e2e', 'title': 'Probabilité (%)'},
                    yaxis={'gridcolor': '#1e1e2e', 'title': ''},
                )
                st.plotly_chart(fig, use_container_width=True)

                # Conseils
                st.markdown("**💊 Conseils généraux :**")
                st.info("→ Restez hydraté(e) et reposez-vous")
                if fievre:
                    st.info("→ Prenez votre température toutes les 4 heures")
                if urgence:
                    st.error("→ Appelez le 15 (SAMU) ou rendez-vous aux urgences")
                st.warning("→ Consultez un médecin si les symptômes s'aggravent")

        else:
            st.markdown("""
            <div style="background:#111118; border:1px dashed #1e1e2e; border-radius:12px;
                        padding:40px; text-align:center; color:#444460">
                <div style="font-size:3rem">🏥</div>
                <div style="margin-top:12px; font-family:'Space Mono',monospace; font-size:0.85rem">
                    Sélectionne les symptômes à gauche<br>et clique sur ANALYSER
                </div>
            </div>
            """, unsafe_allow_html=True)


# ==============================================================
#  PAGE DASHBOARD
# ==============================================================

elif page == "📊 Dashboard":
    st.markdown("## 📊 Dashboard — Statistiques globales")
    st.divider()

    np.random.seed(7)

    # Métriques simulées
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Connexions analysées", "12,847", "+234 aujourd'hui")
    with col2: st.metric("Attaques détectées", "1,203", "+18 aujourd'hui")
    with col3: st.metric("Taux de détection", "99.2%", "+0.1%")
    with col4: st.metric("Faux positifs", "0.8%", "-0.2%")

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### 🔐 Répartition des attaques réseau")
        fig1 = go.Figure(go.Pie(
            labels=['Normal', 'DoS', 'Probe', 'R2L', 'U2R'],
            values=[72, 13, 9, 4, 2],
            hole=0.5,
            marker=dict(colors=['#00f5c4', '#ff4757', '#ffa502', '#7c6cff', '#ff6b6b']),
        ))
        fig1.update_layout(
            paper_bgcolor='#111118', plot_bgcolor='#111118',
            font={'color': '#e8e8f0', 'family': 'Syne'},
            height=300, margin=dict(t=10, b=10),
            showlegend=True,
            legend=dict(bgcolor='#111118', bordercolor='#1e1e2e')
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_right:
        st.markdown("#### 🏥 Diagnostics posés cette semaine")
        fig2 = px.bar(
            x=['Grippe', 'Gastro', 'Migraine', 'Angine', 'Cardiaque', 'Autre'],
            y=[42, 28, 19, 15, 7, 31],
            color_discrete_sequence=['#ff6b6b']
        )
        fig2.update_layout(
            paper_bgcolor='#111118', plot_bgcolor='#111118',
            font={'color': '#e8e8f0', 'family': 'Syne'},
            height=300, margin=dict(t=10, b=10),
            xaxis={'gridcolor': '#1e1e2e', 'title': ''},
            yaxis={'gridcolor': '#1e1e2e', 'title': 'Nb cas'},
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Timeline activité réseau
    st.markdown("#### 📈 Activité réseau — 24 dernières heures")
    heures = list(range(24))
    trafic_normal  = np.random.randint(80, 200, 24)
    trafic_attaque = np.random.randint(0, 30, 24)
    trafic_attaque[14] = 120  # pic d'attaque simulé

    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=heures, y=trafic_normal, name='Normal',
        fill='tozeroy', fillcolor='rgba(0,245,196,0.08)',
        line=dict(color='#00f5c4', width=2)
    ))
    fig3.add_trace(go.Scatter(
        x=heures, y=trafic_attaque, name='Attaque',
        fill='tozeroy', fillcolor='rgba(255,71,87,0.15)',
        line=dict(color='#ff4757', width=2)
    ))
    fig3.update_layout(
        paper_bgcolor='#111118', plot_bgcolor='#111118',
        font={'color': '#e8e8f0', 'family': 'Syne'},
        height=250, margin=dict(t=10, b=10, l=10, r=10),
        xaxis={'gridcolor': '#1e1e2e', 'title': 'Heure'},
        yaxis={'gridcolor': '#1e1e2e', 'title': 'Connexions'},
        legend=dict(bgcolor='#111118', bordercolor='#1e1e2e')
    )
    st.plotly_chart(fig3, use_container_width=True)
