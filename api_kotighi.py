from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
import pickle
import os
from typing import List

# Import des fonctions de chargement de modèles (on réutilise la logique de app_kotighi)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

app = FastAPI(title="KOTIGHI AI API", description="API pour la détection d'intrusion et le diagnostic médical")

# --- SCHÉMAS DE DONNÉES ---
class CyberInput(BaseModel):
    requetes_min: int
    duree: int
    octets: int
    ports_scanes: int
    taux_erreur: float
    flag_suspect: int

class SanteInput(BaseModel):
    fievre: int
    toux: int
    fatigue: int
    maux_tete: int
    douleur_gorge: int
    nausees: int
    douleur_thorax: int
    essoufflement: int
    diarrhee: int
    frissons: int
    perte_odorat: int
    douleurs_musculaires: int
    palpitations: int
    vertiges: int

# --- CHARGEMENT DES MODÈLES (Simulé pour l'exemple API) ---
# En production, il vaut mieux charger des fichiers .pkl pré-entraînés
def load_models():
    # Simulation de chargement rapide
    # Cyber
    np.random.seed(42); N=100
    X = pd.DataFrame(np.random.randint(0,100,(N,6)), columns=["requetes_min","duree","octets","ports_scanes","taux_erreur","flag_suspect"])
    y = np.random.randint(0,2,N)
    sc = StandardScaler(); Xs = sc.fit_transform(X)
    m_cyber = RandomForestClassifier().fit(Xs,y)
    
    # Sante
    cols_sante = ["fievre","toux","fatigue","maux_tete","douleur_gorge","nausees","douleur_thorax","essoufflement","diarrhee","frissons","perte_odorat","douleurs_musculaires","palpitations","vertiges"]
    X_s = pd.DataFrame(np.random.randint(0,2,(N,14)), columns=cols_sante)
    y_s = np.random.randint(0,8,N)
    m_sante = RandomForestClassifier().fit(X_s,y_s)
    labels_sante = ["COVID-19","Grippe","Problème cardiaque","Gastro-entérite","Migraine","Angine","Asthme/Stress","Symptômes non spécifiques"]
    
    return m_cyber, sc, m_sante, labels_sante

m_cyber, sc_cyber, m_sante, labels_sante = load_models()

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "online", "message": "Bienvenue sur l'API KOTIGHI AI"}

@app.post("/predict/cyber")
def predict_cyber(data: CyberInput):
    try:
        feat = pd.DataFrame([data.dict()])
        feat_scaled = sc_cyber.transform(feat)
        pred = int(m_cyber.predict(feat_scaled)[0])
        proba = m_cyber.predict_proba(feat_scaled)[0].tolist()
        
        verdict = "Attaque" if pred == 1 else "Normal"
        return {
            "prediction": pred,
            "verdict": verdict,
            "confiance": round(max(proba) * 100, 2),
            "probabilites": proba
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict/sante")
def predict_sante(data: SanteInput):
    try:
        feat = pd.DataFrame([data.dict()])
        pred = int(m_sante.predict(feat)[0])
        proba = m_sante.predict_proba(feat)[0].tolist()
        
        diag = labels_sante[pred]
        urgent = "cardiaque" in diag.lower() or "covid" in diag.lower()
        
        return {
            "prediction_id": pred,
            "diagnostic": diag,
            "urgent": urgent,
            "confiance": round(proba[pred] * 100, 2),
            "toutes_probabilites": {labels_sante[i]: round(p*100, 2) for i, p in enumerate(proba)}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
