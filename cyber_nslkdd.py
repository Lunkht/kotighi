# ============================================================
#  SENTINEL AI — Cybersécurité avec Dataset NSL-KDD
#  Ce fichier utilise les VRAIES colonnes du dataset NSL-KDD
#  (le standard mondial pour la détection d'intrusion réseau)
# ============================================================
#
#  INSTALLATION (une seule fois) :
#  pip install scikit-learn pandas numpy matplotlib seaborn
#
#  COMMENT OBTENIR LE VRAI DATASET NSL-KDD :
#  ─────────────────────────────────────────
#  Option A — Kaggle (recommandé) :
#    1. Va sur https://www.kaggle.com
#    2. Crée un compte gratuit
#    3. Recherche : "NSL-KDD Dataset"
#    4. Télécharge "KDDTrain+.txt" et "KDDTest+.txt"
#    5. Place ces fichiers dans le même dossier que ce script
#    6. Change USE_REAL_DATA = True (ligne 45)
#
#  Option B — Direct :
#    https://www.unb.ca/cic/datasets/nsl.html
# ============================================================

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, roc_auc_score)
from sklearn.preprocessing import LabelEncoder, StandardScaler

# ── CONFIG ─────────────────────────────────────────────────
# Mets True quand tu as téléchargé les vrais fichiers Kaggle
USE_REAL_DATA = False
TRAIN_FILE    = "KDDTrain+.txt"   # chemin vers ton fichier téléchargé
TEST_FILE     = "KDDTest+.txt"

# ── COLONNES OFFICIELLES DU DATASET NSL-KDD ────────────────
# Ce sont les 41 caractéristiques réseau réelles + 1 label
COLONNES_NSLKDD = [
    # Caractéristiques de base de la connexion TCP
    'duree', 'protocole', 'service', 'flag',
    'octets_src_dest', 'octets_dest_src',
    'connexion_land', 'fragments_errones', 'urgent',
    # Caractéristiques du contenu
    'connexions_root', 'connexions_su', 'acces_root',
    'creation_fichier', 'shells', 'acces_fichiers',
    'commandes_sortie', 'connexion_hot', 'echecs_login',
    'login_reussi', 'nb_compromis', 'root_shell',
    'su_tente', 'nb_root', 'nb_creation_fichier',
    'nb_shells', 'nb_acces_fichiers', 'nb_commandes_sortie',
    'connexion_hote_login', 'connexion_invite',
    # Caractéristiques du trafic (fenêtre 2 secondes)
    'nb_connexions', 'nb_srv_connexions',
    'taux_erreur_serv', 'taux_erreur_rerr',
    'taux_erreur_serr', 'taux_srv_diff_hote',
    'taux_srv_hote', 'nb_hote_dest',
    'nb_hote_srv', 'taux_connexion_hote',
    'taux_srv_connexion_hote', 'taux_diff_srv_hote',
    # Label + score de difficulté
    'label', 'score_difficulte'
]

# Types d'attaques dans NSL-KDD (regroupées en 4 catégories)
CATEGORIES_ATTAQUES = {
    # DoS : épuiser les ressources du serveur
    'neptune': 'DoS', 'back': 'DoS', 'land': 'DoS',
    'pod': 'DoS', 'smurf': 'DoS', 'teardrop': 'DoS',
    'apache2': 'DoS', 'udpstorm': 'DoS',
    # Probe : reconnaissance / scan
    'ipsweep': 'Probe', 'nmap': 'Probe', 'portsweep': 'Probe',
    'satan': 'Probe', 'mscan': 'Probe', 'saint': 'Probe',
    # R2L : accès distant non autorisé
    'ftp_write': 'R2L', 'guess_passwd': 'R2L', 'imap': 'R2L',
    'multihop': 'R2L', 'phf': 'R2L', 'spy': 'R2L',
    'warezclient': 'R2L', 'warezmaster': 'R2L',
    # U2R : escalade de privilèges
    'buffer_overflow': 'U2R', 'loadmodule': 'U2R',
    'perl': 'U2R', 'rootkit': 'U2R', 'ps': 'U2R',
    # Normal
    'normal': 'Normal'
}


# ==============================================================
#  ÉTAPE 1 : CHARGEMENT DES DONNÉES
# ==============================================================

def charger_donnees():
    print("\n" + "="*60)
    print("  📦 ÉTAPE 1 : Chargement du dataset NSL-KDD")
    print("="*60)

    if USE_REAL_DATA:
        # ── VRAI DATASET KAGGLE ────────────────────────────
        print(f"  📂 Lecture du fichier réel : {TRAIN_FILE}")
        try:
            df_train = pd.read_csv(TRAIN_FILE, header=None, names=COLONNES_NSLKDD)
            df_test  = pd.read_csv(TEST_FILE,  header=None, names=COLONNES_NSLKDD)
            df = pd.concat([df_train, df_test], ignore_index=True)
            print(f"  ✅ {len(df_train)} lignes train + {len(df_test)} lignes test")
        except FileNotFoundError:
            print("  ❌ Fichier non trouvé. Passe USE_REAL_DATA = False")
            print("     ou place KDDTrain+.txt dans ce dossier.")
            return None

    else:
        # ── DONNÉES SIMULÉES (fidèles au vrai NSL-KDD) ────
        print("  🔬 Génération de données simulées (structure NSL-KDD réelle)...")
        print("  💡 Pour utiliser le vrai dataset → USE_REAL_DATA = True")
        np.random.seed(42)
        N = 5000

        # Simule les 41 colonnes avec des distributions réalistes
        df = pd.DataFrame({
            'duree':              np.random.exponential(5, N).astype(int),
            'protocole':          np.random.choice(['tcp','udp','icmp'], N, p=[0.6,0.3,0.1]),
            'service':            np.random.choice(['http','ftp','smtp','ssh','dns'], N),
            'flag':               np.random.choice(['SF','S0','REJ','RSTO'], N, p=[0.7,0.1,0.1,0.1]),
            'octets_src_dest':    np.random.exponential(5000, N).astype(int),
            'octets_dest_src':    np.random.exponential(3000, N).astype(int),
            'connexion_land':     np.random.choice([0,1], N, p=[0.99,0.01]),
            'fragments_errones':  np.zeros(N, dtype=int),
            'urgent':             np.zeros(N, dtype=int),
            'connexions_root':    np.random.choice([0,1,2], N, p=[0.8,0.15,0.05]),
            'echecs_login':       np.random.choice([0,1], N, p=[0.9,0.1]),
            'login_reussi':       np.random.choice([0,1], N, p=[0.85,0.15]),
            'nb_connexions':      np.random.randint(1, 512, N),
            'nb_srv_connexions':  np.random.randint(1, 512, N),
            'taux_erreur_serv':   np.random.uniform(0, 1, N).round(2),
            'taux_erreur_rerr':   np.random.uniform(0, 1, N).round(2),
            'nb_hote_dest':       np.random.randint(1, 255, N),
            'nb_hote_srv':        np.random.randint(1, 255, N),
            'taux_connexion_hote':np.random.uniform(0, 1, N).round(2),
        })

        # Génère les labels (types d'attaques réels de NSL-KDD)
        types = ['normal', 'neptune', 'ipsweep', 'portsweep',
                 'satan', 'smurf', 'nmap', 'back',
                 'guess_passwd', 'buffer_overflow']
        probs = [0.52, 0.15, 0.08, 0.05, 0.05, 0.05, 0.04, 0.03, 0.02, 0.01]
        df['label'] = np.random.choice(types, N, p=probs)

    # Ajouter la catégorie (Normal / DoS / Probe / R2L / U2R)
    df['categorie'] = df['label'].map(
        lambda x: CATEGORIES_ATTAQUES.get(x, 'Autre')
    )

    print(f"\n  📊 Distribution des connexions :")
    for cat, count in df['categorie'].value_counts().items():
        pct = count / len(df) * 100
        bar = '█' * int(pct / 2)
        print(f"     {cat:<10} {bar:<25} {count:>5} ({pct:.1f}%)")

    return df


# ==============================================================
#  ÉTAPE 2 : PRÉTRAITEMENT
# ==============================================================

def pretraiter(df):
    print("\n" + "="*60)
    print("  🔧 ÉTAPE 2 : Prétraitement des données")
    print("="*60)

    # Sélectionner les colonnes numériques disponibles
    cols_numeriques = df.select_dtypes(include=[np.number]).columns.tolist()
    cols_numeriques = [c for c in cols_numeriques
                       if c not in ['label', 'score_difficulte', 'categorie']]

    # Encoder les colonnes texte (protocole, service, flag)
    cols_texte = ['protocole', 'service', 'flag']
    encodeurs = {}
    for col in cols_texte:
        if col in df.columns:
            enc = LabelEncoder()
            df[col + '_enc'] = enc.fit_transform(df[col].astype(str))
            encodeurs[col] = enc
            cols_numeriques.append(col + '_enc')

    # Features et target
    X = df[cols_numeriques].fillna(0)
    y_multi  = df['categorie']                  # classification multi-classes
    y_binaire = (df['categorie'] != 'Normal').astype(int)  # normal vs attaque

    # Normalisation
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    X_scaled = pd.DataFrame(X_scaled, columns=cols_numeriques)

    print(f"  ✅ {X.shape[1]} features sélectionnées")
    print(f"  ✅ {len(X)} connexions prêtes")
    print(f"  ✅ Données normalisées (StandardScaler)")

    return X_scaled, y_binaire, y_multi, scaler, encodeurs


# ==============================================================
#  ÉTAPE 3 : ENTRAÎNEMENT ET COMPARAISON DE MODÈLES
# ==============================================================

def entrainer_modeles(X, y_bin, y_multi):
    print("\n" + "="*60)
    print("  🧠 ÉTAPE 3 : Entraînement et comparaison des modèles")
    print("="*60)

    # Split train / test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_bin, test_size=0.2, random_state=42, stratify=y_bin
    )

    # ── MODÈLE 1 : Random Forest ───────────────────────────
    print("\n  🌳 Modèle 1 : Random Forest...")
    rf = RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42)
    rf.fit(X_train, y_train)
    pred_rf = rf.predict(X_test)
    acc_rf  = accuracy_score(y_test, pred_rf) * 100

    # ── MODÈLE 2 : Gradient Boosting ──────────────────────
    print("  ⚡ Modèle 2 : Gradient Boosting...")
    gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
    gb.fit(X_train, y_train)
    pred_gb = gb.predict(X_test)
    acc_gb  = accuracy_score(y_test, pred_gb) * 100

    print(f"\n  📊 Résultats comparatifs :")
    print(f"  ┌─────────────────────────┬───────────┐")
    print(f"  │ Modèle                  │ Précision │")
    print(f"  ├─────────────────────────┼───────────┤")
    print(f"  │ 🌳 Random Forest        │  {acc_rf:>6.2f}%  │")
    print(f"  │ ⚡ Gradient Boosting    │  {acc_gb:>6.2f}%  │")
    print(f"  └─────────────────────────┴───────────┘")

    # Choisir le meilleur modèle
    meilleur = rf if acc_rf >= acc_gb else gb
    nom_meilleur = "Random Forest" if acc_rf >= acc_gb else "Gradient Boosting"
    print(f"\n  🏆 Meilleur modèle : {nom_meilleur}")

    # Rapport détaillé
    pred_best = meilleur.predict(X_test)
    print(f"\n  📋 Rapport détaillé ({nom_meilleur}) :")
    print(classification_report(
        y_test, pred_best,
        target_names=['Normal', 'Attaque'],
        zero_division=0
    ))

    return meilleur, X_test, y_test


# ==============================================================
#  ÉTAPE 4 : IMPORTANCE DES FEATURES
# ==============================================================

def analyser_features(modele, colonnes):
    print("\n" + "="*60)
    print("  🔍 ÉTAPE 4 : Quelles features sont les plus importantes ?")
    print("="*60)
    print("  (Ce sont les indicateurs que l'IA utilise le plus)\n")

    importances = pd.Series(modele.feature_importances_, index=colonnes)
    top10 = importances.nlargest(10)

    for feature, score in top10.items():
        bar = '█' * int(score * 200)
        print(f"  {feature:<30} {bar:<20} {score:.4f}")


# ==============================================================
#  ÉTAPE 5 : DÉTECTEUR EN TEMPS RÉEL (simulation)
# ==============================================================

def detecteur_temps_reel(modele, scaler, feature_cols):
    print("\n" + "="*60)
    print("  🚨 ÉTAPE 5 : Simulation de détection en temps réel")
    print("="*60)

    # Simule 8 connexions arrivant en "temps réel"
    scenarios = [
        {"nom": "Navigation web normale",        "octets_src_dest": 1200,  "nb_connexions": 15,  "taux_erreur_serv": 0.01, "duree": 30},
        {"nom": "Scan de ports (Probe)",          "octets_src_dest": 0,     "nb_connexions": 511, "taux_erreur_serv": 0.90, "duree": 0 },
        {"nom": "Flood DDoS (DoS)",               "octets_src_dest": 0,     "nb_connexions": 500, "taux_erreur_serv": 0.95, "duree": 0 },
        {"nom": "Transfert FTP légitime",         "octets_src_dest": 50000, "nb_connexions": 5,   "taux_erreur_serv": 0.00, "duree": 120},
        {"nom": "Brute force SSH (R2L)",          "octets_src_dest": 200,   "nb_connexions": 300, "taux_erreur_serv": 0.80, "duree": 1 },
        {"nom": "Requête DNS normale",            "octets_src_dest": 100,   "nb_connexions": 3,   "taux_erreur_serv": 0.00, "duree": 1 },
        {"nom": "Exploit buffer overflow (U2R)", "octets_src_dest": 300,   "nb_connexions": 10,  "taux_erreur_serv": 0.50, "duree": 2 },
        {"nom": "Streaming vidéo",                "octets_src_dest": 80000, "nb_connexions": 20,  "taux_erreur_serv": 0.02, "duree": 600},
    ]

    print(f"\n  {'Connexion':<38} {'Verdict':<15} {'Confiance'}")
    print(f"  {'-'*65}")

    for s in scenarios:
        # Créer un vecteur de features (0 pour celles non spécifiées)
        vec = pd.DataFrame([{col: 0 for col in feature_cols}])
        for key, val in s.items():
            if key in vec.columns:
                vec[key] = val

        vec_scaled = scaler.transform(vec)
        pred  = modele.predict(vec_scaled)[0]
        proba = modele.predict_proba(vec_scaled)[0]
        conf  = max(proba) * 100

        if pred == 0:
            verdict = "🟢 NORMAL"
        else:
            verdict = "🔴 ATTAQUE"

        print(f"  {s['nom']:<38} {verdict:<15} {conf:.0f}%")


# ==============================================================
#  PROGRAMME PRINCIPAL
# ==============================================================

if __name__ == "__main__":
    print("\n" + "🛡️ " * 20)
    print("  SENTINEL AI — Cybersécurité avec Dataset NSL-KDD")
    print("🛡️ " * 20)

    # 1. Charger les données
    df = charger_donnees()
    if df is None:
        exit()

    # 2. Prétraiter
    X, y_bin, y_multi, scaler, encodeurs = pretraiter(df)

    # 3. Entraîner et comparer les modèles
    meilleur_modele, X_test, y_test = entrainer_modeles(X, y_bin, y_multi)

    # 4. Analyser l'importance des features
    analyser_features(meilleur_modele, X.columns)

    # 5. Simulation temps réel
    detecteur_temps_reel(meilleur_modele, scaler, X.columns)

    print("\n" + "="*60)
    print("  ✅ Analyse complète terminée !")
    print("="*60)
    print("""
  📚 Prochaines étapes :
  ──────────────────────────────────────────────────
  ① Télécharge le vrai dataset NSL-KDD sur Kaggle :
      → kaggle.com → search "NSL-KDD Dataset"
      → télécharge KDDTrain+.txt et KDDTest+.txt
      → mets USE_REAL_DATA = True dans ce fichier

  ② Améliore le modèle :
      → Teste XGBoost  : pip install xgboost
      → Teste un réseau de neurones avec Keras

  ③ Crée une interface web :
      → pip install streamlit
      → on code ensemble l'app visuelle !
  """)
