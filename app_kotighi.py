import streamlit as st
import pandas as pd
import numpy as np
import hashlib, time
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="KOTIGHI AI", layout="wide")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Space+Mono&display=swap');
html,body,[class*="css"]{font-family:'Syne',sans-serif}
.stApp{background:#0a0a0f;color:#e8e8f0}
[data-testid="stSidebar"]{background:#111118!important;border-right:1px solid #1e1e2e}
[data-testid="metric-container"]{background:#111118;border:1px solid #1e1e2e;border-radius:12px;padding:16px}
.stButton>button{background:linear-gradient(135deg,rgba(0,245,196,.15),rgba(124,108,255,.15));color:#00f5c4;border:1px solid rgba(0,245,196,.4);border-radius:10px;font-family:'Syne',sans-serif;font-weight:700;width:100%}
.stButton>button:hover{background:linear-gradient(135deg,rgba(0,245,196,.3),rgba(124,108,255,.3))}
h1,h2,h3{font-family:'Syne',sans-serif!important}
.stTextInput input{background:#0a0a0f!important;color:#e8e8f0!important;border:1px solid #1e1e2e!important;border-radius:8px!important}
.adanger{background:rgba(255,71,87,.1);border:1px solid rgba(255,71,87,.4);border-radius:10px;padding:16px;color:#ff4757;font-family:'Space Mono',monospace}
.asuccess{background:rgba(0,245,196,.08);border:1px solid rgba(0,245,196,.3);border-radius:10px;padding:16px;color:#00f5c4;font-family:'Space Mono',monospace}
.awarning{background:rgba(255,165,0,.08);border:1px solid rgba(255,165,0,.3);border-radius:10px;padding:16px;color:#ffa502;font-family:'Space Mono',monospace}
.infob{background:rgba(124,108,255,.08);border:1px solid rgba(124,108,255,.2);border-radius:10px;padding:12px 16px;color:#9d8fff;font-family:'Space Mono',monospace;font-size:.8rem}
.ubadge{background:rgba(0,245,196,.08);border:1px solid rgba(0,245,196,.2);border-radius:10px;padding:10px 14px;font-family:'Space Mono',monospace;font-size:.78rem;color:#00f5c4}
</style>""", unsafe_allow_html=True)

# ── AUTH ──────────────────────────────────────────────────────────
def h(p): return hashlib.sha256(p.encode()).hexdigest()

USERS = {
    "admin":    {"hash":h("kotighi2024"),"role":"Administrateur","nom":"Admin Principal",   "acces":["Accueil","Cybersecurite","Sante","Dashboard","Gestion"]},
    "analyste": {"hash":h("analyse123"), "role":"Analyste Cyber", "nom":"Analyste Securite","acces":["Accueil","Cybersecurite","Dashboard"]},
    "medecin":  {"hash":h("sante456"),   "role":"Medecin",        "nom":"Praticien Medical","acces":["Accueil","Sante","Dashboard"]},
}

def verifier(login, mdp):
    l = login.strip().lower()
    if l in USERS and USERS[l]["hash"] == h(mdp): return USERS[l]
    return None

for k,v in {"connecte":False,"utilisateur":None,"login_nom":None,"tentatives":0,"historique":[]}.items():
    if k not in st.session_state: st.session_state[k] = v

# ── MODELES ───────────────────────────────────────────────────────
@st.cache_resource
def get_cyber():
    np.random.seed(42); N=3000
    cols = ["requetes_min","duree","octets","ports_scanes","taux_erreur","flag_suspect"]
    n = pd.DataFrame({"requetes_min":np.random.randint(5,300,N//2),"duree":np.random.randint(10,120,N//2),"octets":np.random.randint(500,10000,N//2),"ports_scanes":np.random.randint(1,4,N//2),"taux_erreur":np.random.uniform(0,.1,N//2),"flag_suspect":np.zeros(N//2)})
    a = pd.DataFrame({"requetes_min":np.random.randint(500,8000,N//2),"duree":np.random.randint(0,5,N//2),"octets":np.random.randint(10,300,N//2),"ports_scanes":np.random.randint(20,200,N//2),"taux_erreur":np.random.uniform(.5,1.,N//2),"flag_suspect":np.ones(N//2)})
    df = pd.concat([n.assign(label=0),a.assign(label=1)]).sample(frac=1,random_state=42)
    X,y = df.drop("label",axis=1),df["label"]
    sc = StandardScaler(); Xs = sc.fit_transform(X)
    m = RandomForestClassifier(n_estimators=150,random_state=42,n_jobs=-1); m.fit(Xs,y)
    return m,sc

@st.cache_resource
def get_sante():
    np.random.seed(99); N=2000
    cols = ["fievre","toux","fatigue","maux_tete","douleur_gorge","nausees","douleur_thorax","essoufflement","diarrhee","frissons"]
    d = pd.DataFrame({c:np.random.randint(0,2,N) for c in cols})
    def diag(r):
        if r["fievre"] and r["toux"] and r["fatigue"]: return 0
        if r["douleur_thorax"] and r["essoufflement"]: return 1
        if r["nausees"] and r["diarrhee"]: return 2
        if r["maux_tete"] and r["fatigue"]: return 3
        if r["douleur_gorge"] and r["fievre"]: return 4
        return 5
    d["label"] = d.apply(diag,axis=1)
    m = RandomForestClassifier(n_estimators=100,random_state=42); m.fit(d.drop("label",axis=1),d["label"])
    return m,["Grippe","Probleme cardiaque","Gastro-enterite","Migraine","Angine","Symptomes non specifiques"]

# ── PAGE LOGIN ────────────────────────────────────────────────────
def page_login():
    st.markdown("""<div style='text-align:center;padding:40px 0 10px'>
        <div style='font-family:Syne,sans-serif;font-size:2.5rem;font-weight:800;background:linear-gradient(90deg,#00f5c4,#7c6cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>KOTIGHI AI</div>
        <div style='font-family:Space Mono,monospace;font-size:.75rem;color:#666680;letter-spacing:3px;margin-top:6px'>CYBERSECURITE ET SANTE</div>
    </div>""", unsafe_allow_html=True)
    _,col,_ = st.columns([1,1.2,1])
    with col:
        st.markdown("""<div style='background:#111118;border:1px solid #1e1e2e;border-radius:20px;padding:36px 32px;margin-top:20px'>
            <div style='font-size:1.1rem;font-weight:700;margin-bottom:4px'>Connexion</div>
            <div style='font-family:Space Mono,monospace;font-size:.75rem;color:#666680;margin-bottom:24px'>Identifiez-vous pour acceder a la plateforme</div>
        </div>""", unsafe_allow_html=True)
        if st.session_state.tentatives >= 5:
            st.markdown("<div class='adanger'>Trop de tentatives. Compte bloque. Contactez l&#39;administrateur.</div>", unsafe_allow_html=True)
            return
        login    = st.text_input("Identifiant", placeholder="Votre login")
        password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
        if st.button("SE CONNECTER", type="primary"):
            if not login or not password:
                st.warning("Veuillez remplir tous les champs.")
            else:
                user = verifier(login, password)
                if user:
                    st.session_state.connecte = True
                    st.session_state.utilisateur = user
                    st.session_state.login_nom = login.lower()
                    st.session_state.tentatives = 0
                    st.success("Connexion reussie.")
                    time.sleep(0.8); st.rerun()
                else:
                    st.session_state.tentatives += 1
                    r = 5 - st.session_state.tentatives
                    st.markdown(f"<div class='adanger'>Identifiant ou mot de passe incorrect. Tentatives restantes : {r}</div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:20px;font-family:Space Mono,monospace;font-size:.72rem;color:#444460;text-align:center'>Comptes demo :<br>admin / kotighi2024 &nbsp;|&nbsp; analyste / analyse123 &nbsp;|&nbsp; medecin / sante456</div>", unsafe_allow_html=True)

# ── APP PRINCIPALE ────────────────────────────────────────────────
def app():
    user  = st.session_state.utilisateur
    login = st.session_state.login_nom

    with st.sidebar:
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
            with c1: st.markdown("<div style='background:#111118;border:1px solid #1e1e2e;border-radius:16px;padding:24px'><div style='font-size:1.1rem;font-weight:700;color:#00f5c4;margin-bottom:8px'>Module Cybersecurite</div><div style='color:#888;font-size:.88rem;line-height:1.7'>Detection d&#39;intrusions, DDoS, scans de ports et brute force.</div></div>", unsafe_allow_html=True)
        if "Sante" in user["acces"]:
            with c2: st.markdown("<div style='background:#111118;border:1px solid #1e1e2e;border-radius:16px;padding:24px'><div style='font-size:1.1rem;font-weight:700;color:#ff6b6b;margin-bottom:8px'>Module Sante</div><div style='color:#888;font-size:.88rem;line-height:1.7'>Analyse des symptomes et prediction parmi 6 pathologies.</div></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.metric("Precision cyber","98%+","NSL-KDD reel")
        with c2: st.metric("Precision sante","95%+","donnees reelles")
        with c3: st.metric("Types attaques","5","DoS,Probe,R2L...")
        with c4: st.metric("Symptomes","10","par module sante")

    # CYBERSECURITE
    elif page == "Cybersecurite":
        st.markdown("## Detection d'intrusion reseau"); st.divider()
        mc,sc = get_cyber()
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
            st.markdown("### Resultat")
            if go_c:
                feat = pd.DataFrame([{"requetes_min":req,"duree":dur,"octets":oct_,"ports_scanes":ports,"taux_erreur":terr,"flag_suspect":int(flag)}])
                pred  = mc.predict(sc.transform(feat))[0]
                proba = mc.predict_proba(sc.transform(feat))[0]
                conf  = max(proba)*100
                if pred==0:
                    type_att="Normal"
                    st.markdown(f"<div class='asuccess'><strong>CONNEXION NORMALE</strong><br>Aucune menace — Confiance : {conf:.0f}%</div>",unsafe_allow_html=True)
                else:
                    type_att = "DoS/DDoS" if req>2000 else ("Scan de ports" if ports>30 else ("Brute Force" if terr>0.7 else "Activite suspecte"))
                    st.markdown(f"<div class='adanger'><strong>ATTAQUE — {type_att}</strong><br>Confiance : {conf:.0f}% — IP : {ip}</div>",unsafe_allow_html=True)
                fig = go.Figure(go.Indicator(mode="gauge+number",value=proba[1]*100,
                    title={"text":"Score de Risque","font":{"color":"#e8e8f0","family":"Syne"}},
                    gauge={"axis":{"range":[0,100]},"bar":{"color":"#ff4757" if pred==1 else "#00f5c4"},"bgcolor":"#111118","bordercolor":"#1e1e2e",
                           "steps":[{"range":[0,30],"color":"rgba(0,245,196,.1)"},{"range":[30,60],"color":"rgba(255,165,0,.1)"},{"range":[60,100],"color":"rgba(255,71,87,.1)"}]},
                    number={"font":{"color":"#e8e8f0"},"suffix":"%"}))
                fig.update_layout(paper_bgcolor="#111118",height=260,margin=dict(t=40,b=0,l=20,r=20),font={"color":"#e8e8f0"})
                st.plotly_chart(fig,use_container_width=True)
                st.session_state.historique.append({"Module":"Cybersecurite","Resultat":type_att,"Confiance":f"{conf:.0f}%","Detail":f"IP {ip} {req}req/min","Utilisateur":login})
                if pred==1: st.error("Bloquer l'IP source"); st.warning("Analyser les logs")
                else: st.success("Connexion autorisee")

    # SANTE
    elif page == "Sante":
        st.markdown("## Analyse de symptomes")
        st.markdown("<div class='awarning'>Outil educatif. Consultez un medecin.</div>",unsafe_allow_html=True)
        st.divider()
        ms,labels = get_sante()
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("### Symptomes du patient")
            age   = st.number_input("Age",1,120,35)
            dur_s = st.selectbox("Duree",["Moins de 24h","1 a 3 jours","3 a 7 jours","Plus d'une semaine"])
            st.markdown("**Symptomes presents :**")
            s1,s2 = st.columns(2)
            with s1:
                fievre=st.checkbox("Fievre"); toux=st.checkbox("Toux"); fat=st.checkbox("Fatigue")
                tete=st.checkbox("Maux de tete"); gorge=st.checkbox("Douleur gorge")
            with s2:
                nau=st.checkbox("Nausees"); thor=st.checkbox("Douleur thoracique")
                ess=st.checkbox("Essoufflement"); diar=st.checkbox("Diarrhee"); fri=st.checkbox("Frissons")
            go_s = st.button("ANALYSER LES SYMPTOMES",type="primary")
        with col2:
            st.markdown("### Resultat")
            if go_s:
                nb = sum([fievre,toux,fat,tete,gorge,nau,thor,ess,diar,fri])
                if nb==0: st.warning("Selectionne au moins un symptome.")
                else:
                    feat = pd.DataFrame([{"fievre":int(fievre),"toux":int(toux),"fatigue":int(fat),"maux_tete":int(tete),"douleur_gorge":int(gorge),"nausees":int(nau),"douleur_thorax":int(thor),"essoufflement":int(ess),"diarrhee":int(diar),"frissons":int(fri)}])
                    pred=ms.predict(feat)[0]; proba=ms.predict_proba(feat)[0]
                    diag=labels[pred]; conf=proba[pred]*100; urgent="cardiaque" in diag
                    if urgent: st.markdown(f"<div class='adanger'><strong>CONSULTATION URGENTE</strong><br>Diagnostic : {diag}<br>Confiance : {conf:.0f}%</div>",unsafe_allow_html=True)
                    else: st.markdown(f"<div class='asuccess'><strong>Diagnostic : {diag}</strong><br>Confiance : {conf:.0f}% — {nb} symptome(s)</div>",unsafe_allow_html=True)
                    df_p = pd.DataFrame({"Diagnostic":labels,"Probabilite":proba*100}).sort_values("Probabilite",ascending=True)
                    fig = px.bar(df_p,x="Probabilite",y="Diagnostic",orientation="h",color="Probabilite",color_continuous_scale=["#1e1e2e","#7c6cff","#ff6b6b"])
                    fig.update_layout(paper_bgcolor="#111118",height=290,margin=dict(t=10,b=10),font={"color":"#e8e8f0","family":"Syne"},showlegend=False,coloraxis_showscale=False,xaxis={"gridcolor":"#1e1e2e","title":"Probabilite (%)"},yaxis={"gridcolor":"#1e1e2e","title":""})
                    st.plotly_chart(fig,use_container_width=True)
                    st.session_state.historique.append({"Module":"Sante","Resultat":diag,"Confiance":f"{conf:.0f}%","Detail":f"Age {age} {nb} symptomes","Utilisateur":login})
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
            st.dataframe(pd.DataFrame(st.session_state.historique[::-1]),use_container_width=True,hide_index=True)
        else:
            st.markdown("<div class='infob'>Aucune analyse effectuee. Lancez une analyse depuis Cybersecurite ou Sante.</div>",unsafe_allow_html=True)

    # GESTION
    elif page == "Gestion":
        st.markdown("## Gestion des utilisateurs"); st.divider()
        df_u = pd.DataFrame([{"Login":k,"Nom":v["nom"],"Role":v["role"],"Modules":", ".join(v["acces"])} for k,v in USERS.items()])
        st.dataframe(df_u,use_container_width=True,hide_index=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.markdown("<div class='infob'>Pour ajouter un utilisateur : ajouter une entree dans USERS avec h() pour le mot de passe.<br><br>En production : utiliser PostgreSQL ou Firebase Auth.</div>",unsafe_allow_html=True)

# ── POINT D'ENTREE ────────────────────────────────────────────────
if not st.session_state.connecte:
    page_login()
else:
    app()