# 🛡️ SENTINEL AI — Cybersécurité & Santé

Plateforme d'intelligence artificielle combinant **détection d'intrusion réseau** et **analyse médicale de symptômes**.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![Scikit-learn](https://img.shields.io/badge/Scikit--learn-1.3+-orange)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Démo en ligne

👉 **[Ouvrir l'application](https://ton-app.streamlit.app)** ← remplace par ton URL après déploiement

---

## ✨ Fonctionnalités

### 🔐 Module Cybersécurité
- Analyse du trafic réseau en temps réel
- Détection de 5 types d'attaques : DoS, DDoS, Probe, R2L, U2R
- Score de risque avec jauge interactive
- Recommandations automatiques

### 🏥 Module Santé
- Analyse de 10 symptômes médicaux
- Prédiction de 6 pathologies avec probabilités
- Alerte urgence pour cas critiques
- Graphique de confiance par diagnostic

### 📊 Dashboard
- Statistiques d'activité réseau 24h
- Répartition des types d'attaques
- Historique des diagnostics

---

## 🛠️ Installation locale

```bash
# 1. Clone le dépôt
git clone https://github.com/TON_USERNAME/sentinel-ai.git
cd sentinel-ai

# 2. Installe les dépendances
pip install -r requirements.txt

# 3. Lance l'application
streamlit run app_sentinel.py
```

L'app s'ouvre sur → **http://localhost:8501**

---

## 📁 Structure du projet

```
sentinel-ai/
│
├── app_sentinel.py       ← Application web principale (Streamlit)
├── sentinel_ai.py        ← Modèles IA de base
├── cyber_nslkdd.py       ← Module cybersécurité avancé (NSL-KDD)
├── requirements.txt      ← Dépendances Python
├── .streamlit/
│   └── config.toml       ← Configuration thème sombre
└── README.md             ← Ce fichier
```

---

## 🧠 Technologies utilisées

| Outil | Usage |
|-------|-------|
| **Python 3.9+** | Langage principal |
| **Streamlit** | Interface web |
| **Scikit-learn** | Modèles IA (Random Forest) |
| **Plotly** | Graphiques interactifs |
| **Pandas / NumPy** | Manipulation des données |

---

## 📚 Dataset

- **Cybersécurité** : [NSL-KDD Dataset](https://www.kaggle.com/datasets/hassan06/nslkdd) — standard mondial pour la détection d'intrusion
- **Santé** : Données simulées (à remplacer par un dataset certifié en production)

---

## ⚠️ Avertissement

> Ce projet est **éducatif**. Il ne remplace pas un expert en cybersécurité ni un médecin professionnel. Ne pas utiliser en environnement de production sans validation par des experts.

---

## 👤 Auteur

Fait avec ❤️ et Python · Propulsé par [Streamlit](https://streamlit.io)
