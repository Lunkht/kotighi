# ============================================================
#  KOTIGHI AI — Ton premier modèle d'IA en Python
#  Modules : Cybersécurité + Santé
#  Niveau   : Débutant
#  Auteur   : Toi 🚀 (avec l'aide de Claude)
# ============================================================
#
#  COMMENT UTILISER CE FICHIER :
#  1. Installe Python sur ton PC : https://python.org
#  2. Installe les bibliothèques nécessaires :
#       pip install scikit-learn pandas numpy
#  3. Lance le fichier :
#       python kotighi_ai.py
#
# ============================================================

# ── Importation des bibliothèques ──────────────────────────
# pandas  = manipuler des tableaux de données
# numpy   = calculs mathématiques
# sklearn = outils d'intelligence artificielle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier   # notre algorithme IA
from sklearn.model_selection import train_test_split  # diviser données en train/test
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import LabelEncoder        # convertir texte → chiffres


# ==============================================================
#  MODULE 1 : CYBERSÉCURITÉ — Détection d'intrusion réseau
# ==============================================================
#
#  L'idée : on donne à l'IA des données sur des connexions réseau
#  (nombre de requêtes, protocole, etc.) et elle apprend à
#  dire si c'est NORMAL ou une ATTAQUE.
#
#  En vrai projet, tu utiliserais le dataset NSL-KDD (Kaggle).
#  Ici on crée des données simulées pour apprendre le concept.

def module_cybersecurite():
    print("\n" + "="*55)
    print("MODULE CYBERSÉCURITÉ — Détection d'intrusion")
    print("="*55)

    # ── ÉTAPE 1 : Créer les données d'entraînement ─────────
    # Chaque ligne = une connexion réseau
    # Colonnes : requetes/min, durée (sec), taille paquets, label
    print("\n📦 Étape 1 : Création des données d'entraînement...")

    np.random.seed(42)  # pour avoir toujours les mêmes résultats

    # Connexions NORMALES (600 exemples)
    normales = pd.DataFrame({
        'requetes_par_min': np.random.randint(10, 200, 600),
        'duree_connexion':  np.random.randint(1, 60, 600),
        'taille_paquets':   np.random.randint(100, 1500, 600),
        'ports_differents': np.random.randint(1, 5, 600),
        'label': 0  # 0 = normal
    })

    # Connexions ATTAQUES (400 exemples)
    attaques = pd.DataFrame({
        'requetes_par_min': np.random.randint(800, 5000, 400),  # beaucoup de requêtes
        'duree_connexion':  np.random.randint(1, 10, 400),       # connexions très courtes
        'taille_paquets':   np.random.randint(50, 200, 400),     # petits paquets
        'ports_differents': np.random.randint(10, 100, 400),     # scan de nombreux ports
        'label': 1  # 1 = attaque
    })

    # On combine les deux en un seul tableau
    donnees = pd.concat([normales, attaques], ignore_index=True)
    donnees = donnees.sample(frac=1).reset_index(drop=True)  # mélanger

    print(f"   ✅ {len(donnees)} connexions chargées")
    print(f"   • Normales  : {len(normales)}")
    print(f"   • Attaques  : {len(attaques)}")

    # ── ÉTAPE 2 : Préparer les données pour l'IA ───────────
    print("\n🔧 Étape 2 : Préparation des données...")

    # X = les caractéristiques (ce que l'IA observe)
    # y = la réponse correcte (normal ou attaque)
    X = donnees[['requetes_par_min', 'duree_connexion', 'taille_paquets', 'ports_differents']]
    y = donnees['label']

    # On divise : 80% pour entraîner, 20% pour tester
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"   ✅ Données divisées : {len(X_train)} train / {len(X_test)} test")

    # ── ÉTAPE 3 : Entraîner le modèle IA ───────────────────
    print("\n🧠 Étape 3 : Entraînement du modèle IA...")

    # Random Forest = un ensemble d'arbres de décision
    # n_estimators = nombre d'arbres (plus = meilleur mais plus lent)
    modele_cyber = RandomForestClassifier(n_estimators=100, random_state=42)
    modele_cyber.fit(X_train, y_train)  # ← C'est ici que l'IA "apprend" !

    print("   ✅ Modèle entraîné !")

    # ── ÉTAPE 4 : Évaluer les performances ─────────────────
    print("\n📊 Étape 4 : Évaluation des performances...")

    predictions = modele_cyber.predict(X_test)
    precision = accuracy_score(y_test, predictions) * 100

    print(f"   🎯 Précision globale : {precision:.1f}%")
    print("\n   Rapport détaillé :")
    print(classification_report(y_test, predictions,
          target_names=['Normal', 'Attaque'],
          zero_division=0))

    # ── ÉTAPE 5 : Tester avec de nouvelles connexions ──────
    print("\n🧪 Étape 5 : Test sur de nouvelles connexions...")

    nouvelles_connexions = pd.DataFrame({
        'requetes_par_min': [50,   2500,  120,  4000],
        'duree_connexion':  [30,   3,     45,   2  ],
        'taille_paquets':   [1200, 80,    900,  60 ],
        'ports_differents': [2,    50,    3,    80 ],
    })

    resultats = modele_cyber.predict(nouvelles_connexions)
    probas    = modele_cyber.predict_proba(nouvelles_connexions)

    labels = ['🟢 NORMAL', '🔴 ATTAQUE']
    for i, (r, p) in enumerate(zip(resultats, probas)):
        conf = max(p) * 100
        print(f"   Connexion {i+1}: {labels[r]}  (confiance: {conf:.0f}%)")

    return modele_cyber


# ==============================================================
#  MODULE 2 : SANTÉ — Prédiction de maladie
# ==============================================================
#
#  L'idée : on donne à l'IA des symptômes d'un patient et elle
#  prédit quelle maladie il pourrait avoir.
#
#  En vrai projet : dataset Kaggle "Disease Symptom Prediction"
#  Ici : données simulées pour comprendre le principe.

def module_sante():
    print("\n" + "="*55)
    print("MODULE SANTÉ — Prédiction de maladie")
    print("="*55)

    # ── ÉTAPE 1 : Créer les données ─────────────────────────
    print("\n📦 Étape 1 : Chargement des données médicales...")

    np.random.seed(123)
    n = 800  # nombre de patients simulés

    # Symptômes (1 = présent, 0 = absent)
    donnees = pd.DataFrame({
        'fievre':          np.random.randint(0, 2, n),
        'toux':            np.random.randint(0, 2, n),
        'fatigue':         np.random.randint(0, 2, n),
        'maux_tete':       np.random.randint(0, 2, n),
        'douleur_gorge':   np.random.randint(0, 2, n),
        'nausees':         np.random.randint(0, 2, n),
        'douleur_thorax':  np.random.randint(0, 2, n),
        'essoufflement':   np.random.randint(0, 2, n),
    })

    # On crée le diagnostic en fonction des symptômes (règles médicales simplifiées)
    def diagnostiquer(row):
        if row['fievre'] and row['toux'] and row['fatigue']:
            return 'Grippe'
        elif row['douleur_thorax'] and row['essoufflement']:
            return 'Problème cardiaque'
        elif row['nausees'] and row['fatigue'] and not row['fievre']:
            return 'Gastrite'
        elif row['maux_tete'] and row['fatigue'] and not row['fievre']:
            return 'Migraine'
        elif row['douleur_gorge'] and row['fievre']:
            return 'Angine'
        else:
            return 'Symptômes non spécifiques'

    donnees['diagnostic'] = donnees.apply(diagnostiquer, axis=1)

    print(f"   ✅ {len(donnees)} dossiers patients chargés")
    print("\n   Distribution des diagnostics :")
    for diag, count in donnees['diagnostic'].value_counts().items():
        print(f"   • {diag} : {count} cas")

    # ── ÉTAPE 2 : Préparer les données ──────────────────────
    print("\n🔧 Étape 2 : Préparation...")

    X = donnees.drop('diagnostic', axis=1)
    y = donnees['diagnostic']

    # Convertir les labels texte en chiffres (obligatoire pour sklearn)
    encodeur = LabelEncoder()
    y_encoded = encodeur.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42
    )
    print(f"   ✅ {len(X_train)} train / {len(X_test)} test")

    # ── ÉTAPE 3 : Entraîner le modèle ───────────────────────
    print("\n🧠 Étape 3 : Entraînement du modèle...")

    modele_sante = RandomForestClassifier(n_estimators=100, random_state=42)
    modele_sante.fit(X_train, y_train)
    print("   ✅ Modèle entraîné !")

    # ── ÉTAPE 4 : Évaluation ────────────────────────────────
    print("\n📊 Étape 4 : Performances du modèle...")

    predictions = modele_sante.predict(X_test)
    precision   = accuracy_score(y_test, predictions) * 100
    print(f"   🎯 Précision : {precision:.1f}%")

    # ── ÉTAPE 5 : Nouveau patient ────────────────────────────
    print("\n🧪 Étape 5 : Diagnostic de nouveaux patients...")

    #                     fiev  toux  fat  tete  gorg  naus  thor  esso
    patients_test = pd.DataFrame({
        'fievre':         [1,    0,    0,   1,   ],
        'toux':           [1,    0,    0,   0,   ],
        'fatigue':        [1,    1,    0,   1,   ],
        'maux_tete':      [0,    0,    1,   0,   ],
        'douleur_gorge':  [0,    0,    0,   0,   ],
        'nausees':        [0,    1,    0,   0,   ],
        'douleur_thorax': [0,    0,    1,   0,   ],
        'essoufflement':  [0,    0,    1,   0,   ],
    })

    descriptions = [
        "Fièvre + toux + fatigue",
        "Fatigue + nausées",
        "Douleur thoracique + essoufflement",
        "Fatigue + maux de tête",
    ]

    preds  = modele_sante.predict(patients_test)
        
    for i, (pred, desc) in enumerate(zip(preds, descriptions)):
        diag = encodeur.inverse_transform([pred])[0]
        urgence = " ⚠️ URGENT" if "cardiaque" in diag else ""
        print(f"   Patient {i+1} ({desc})")
        print(f"   → Diagnostic : {diag}{urgence}\n")

    return modele_sante, encodeur


# ==============================================================
#  PROGRAMME PRINCIPAL
# ==============================================================

if __name__ == "__main__":
    print("\n" + "🛡️ " * 18)
    print("   KOTIGHI AI — Plateforme IA Cybersécurité & Santé")
    print("🛡️ " * 18)

    # Lancer le module cybersécurité
    modele_cyber = module_cybersecurite()

    # Lancer le module santé
    modele_sante, encodeur = module_sante()

    print("\n" + "="*55)
    print("  ✅ Les deux modèles IA sont opérationnels !")
    print("="*55)
    print("""
  📚 Pour aller plus loin :
  ─────────────────────────────────────────────
  1. Remplace les données simulées par de vrais datasets :
     • Cybersécurité : kaggle.com → NSL-KDD Dataset
     • Santé         : kaggle.com → Disease Symptom Dataset

  2. Essaie d'autres algorithmes :
     • from sklearn.svm import SVC
     • from sklearn.neighbors import KNeighborsClassifier

  3. Crée une interface web avec Streamlit :
     • pip install streamlit
     • streamlit run app_kotighi.py

  4. Ressource gratuite pour apprendre :
     • scikit-learn.org/stable/tutorial
    """)
