# ============================================================
#  KOTIGHI AI — Module generation de rapports PDF
#  Fichier : rapport_pdf.py
# ============================================================
#
#  INSTALLATION :
#  pip install reportlab
#
#  UTILISATION dans app_kotighi.py :
#
#    from rapport_pdf import generer_rapport_cyber, generer_rapport_sante
#
#    # Apres une analyse cybersecurite :
#    pdf = generer_rapport_cyber(data)
#    st.download_button("Telecharger le rapport PDF", pdf,
#        file_name="rapport_cyber.pdf", mime="application/pdf")
#
#    # Apres une analyse medicale :
#    pdf = generer_rapport_sante(data)
#    st.download_button("Telecharger le rapport PDF", pdf,
#        file_name="rapport_sante.pdf", mime="application/pdf")
# ============================================================

import io
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors

W, H = A4

# Palette KOTIGHI
C_BG      = colors.HexColor("#0a0a0f")
C_SURFACE = colors.HexColor("#111118")
C_BORDER  = colors.HexColor("#1e1e2e")
C_CYAN    = colors.HexColor("#00f5c4")
C_PURPLE  = colors.HexColor("#7c6cff")
C_RED     = colors.HexColor("#ff4757")
C_ORANGE  = colors.HexColor("#ffa502")
C_HEALTH  = colors.HexColor("#ff6b6b")
C_MUTED   = colors.HexColor("#666680")
C_WHITE   = colors.HexColor("#e8e8f0")
C_DARK_R  = colors.HexColor("#2a0a0e")
C_DARK_G  = colors.HexColor("#0a1a16")
C_DARK_O  = colors.HexColor("#1a1208")


# ── Helpers ──────────────────────────────────────────────────

def _header(c, sous_titre, utilisateur, role, accent):
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    c.setFillColor(C_BG)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(C_SURFACE)
    c.rect(0, H-80, W, 80, fill=1, stroke=0)
    c.setStrokeColor(accent)
    c.setLineWidth(1.5)
    c.line(0, H-80, W, H-80)
    c.setFillColor(accent)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(40, H-45, "KOTIGHI AI")
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(40, H-62, sous_titre)
    c.drawRightString(W-40, H-45, f"Genere le {now}")
    c.drawRightString(W-40, H-62, f"Utilisateur : {utilisateur} ({role})")


def _separateur(c, y):
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.line(40, y, W-40, y)


def _titre_section(c, y, texte, couleur=None):
    c.setFillColor(couleur or C_CYAN)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, texte)
    _separateur(c, y-6)


def _lignes(c, y, rows, col1_w=210):
    for i, (label, val) in enumerate(rows):
        c.setFillColor(C_SURFACE if i % 2 == 0 else C_BG)
        c.rect(40, y-6, W-80, 22, fill=1, stroke=0)
        c.setFillColor(C_MUTED)
        c.setFont("Helvetica", 9)
        c.drawString(50, y+6, label)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50+col1_w, y+6, str(val))
        y -= 22
    return y


def _footer(c):
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    c.setFillColor(C_SURFACE)
    c.rect(0, 0, W, 35, fill=1, stroke=0)
    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.line(0, 35, W, 35)
    c.setFillColor(colors.HexColor("#444460"))
    c.setFont("Helvetica", 7.5)
    c.drawCentredString(W/2, 13,
        f"KOTIGHI AI v1.1 — {now} — Prototype educatif. "
        "Ne remplace pas un expert en securite ni un medecin.")


# ══════════════════════════════════════════════════════════════
#  RAPPORT CYBERSECURITE
# ══════════════════════════════════════════════════════════════

def generer_rapport_cyber(data: dict) -> bytes:
    """
    Genere un rapport PDF pour une analyse cybersecurite.

    Parametres attendus dans data :
        ip           : str   - adresse IP source
        requetes     : int   - requetes par minute
        duree        : int   - duree en secondes
        octets       : int   - octets transferes
        ports        : int   - nombre de ports scannes
        taux_erreur  : float - taux d erreur (0.0 a 1.0)
        prediction   : int   - 0=normal, 1=attaque
        type_attaque : str   - type d attaque detecte
        confiance    : float - confiance du modele (0 a 100)
        utilisateur  : str   - login
        role         : str   - role

    Retourne : bytes du PDF
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    is_attack = data.get("prediction", 0) == 1

    _header(c, "Rapport d'Analyse — Detection d'Intrusion Reseau",
            data.get("utilisateur","N/A"), data.get("role","N/A"), C_CYAN)

    # Verdict
    brd = C_RED if is_attack else C_CYAN
    c.setFillColor(C_DARK_R if is_attack else C_DARK_G)
    c.roundRect(40, H-185, W-80, 75, 8, fill=1, stroke=0)
    c.setStrokeColor(brd)
    c.setLineWidth(1.5)
    c.roundRect(40, H-185, W-80, 75, 8, fill=0, stroke=1)
    verdict = (f"ATTAQUE DETECTEE — {data.get('type_attaque','?')}"
               if is_attack else "CONNEXION NORMALE")
    c.setFillColor(brd)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(W/2, H-153, verdict)
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H-173,
        f"Confiance du modele IA : {data.get('confiance',0):.0f}%")

    # Parametres
    y = H-220
    _titre_section(c, y, "Parametres de la connexion analysee")
    y -= 22
    y = _lignes(c, y, [
        ("Adresse IP source",   data.get("ip","N/A")),
        ("Requetes par minute", str(data.get("requetes",0))),
        ("Duree de connexion",  f"{data.get('duree',0)} secondes"),
        ("Octets transferes",   str(data.get("octets",0))),
        ("Ports scannes",       str(data.get("ports",0))),
        ("Taux d erreur",       f"{data.get('taux_erreur',0):.0%}"),
    ])

    # Recommandations
    y -= 20
    _titre_section(c, y, "Recommandations")
    if is_attack:
        recs = [
            (C_RED,    "CRITIQUE",  "Bloquer immediatement l'IP source au pare-feu."),
            (C_RED,    "CRITIQUE",  "Alerter l'equipe securite (SOC) et ouvrir un incident."),
            (C_ORANGE, "IMPORTANT", "Analyser les logs complets de la session reseau."),
            (C_ORANGE, "IMPORTANT", "Verifier les systemes potentiellement affectes."),
            (C_PURPLE, "CONSEIL",   "Conserver les preuves pour analyse forensique."),
        ]
    else:
        recs = [
            (C_CYAN,   "OK",      "Connexion autorisee — aucune action requise."),
            (C_PURPLE, "CONSEIL", "Continuer la surveillance de routine."),
            (C_PURPLE, "CONSEIL", "Journaliser l'analyse pour le rapport mensuel."),
        ]
    y -= 22
    for i, (col, niv, txt) in enumerate(recs):
        c.setFillColor(C_SURFACE if i % 2 == 0 else C_BG)
        c.rect(40, y-6, W-80, 22, fill=1, stroke=0)
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, y+6, niv)
        c.setFillColor(C_WHITE)
        c.setFont("Helvetica", 9)
        c.drawString(170, y+6, txt)
        y -= 22

    _footer(c)
    c.save()
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════
#  RAPPORT SANTE
# ══════════════════════════════════════════════════════════════

def generer_rapport_sante(data: dict) -> bytes:
    """
    Genere un rapport PDF pour une analyse medicale.

    Parametres attendus dans data :
        age             : int   - age du patient
        duree_symptomes : str   - duree des symptomes
        symptomes       : list  - liste des symptomes presents
        diagnostic      : str   - diagnostic probable
        confiance       : float - confiance du modele (0 a 100)
        urgent          : bool  - cas urgent ou non
        utilisateur     : str   - login
        role            : str   - role

    Retourne : bytes du PDF
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    urgent = data.get("urgent", False)

    _header(c, "Rapport d'Analyse Medicale — Symptomes",
            data.get("utilisateur","N/A"), data.get("role","N/A"), C_HEALTH)

    # Avertissement
    brd = C_RED if urgent else C_ORANGE
    c.setFillColor(C_DARK_R if urgent else C_DARK_O)
    c.roundRect(40, H-185, W-80, 75, 8, fill=1, stroke=0)
    c.setStrokeColor(brd)
    c.setLineWidth(1.5)
    c.roundRect(40, H-185, W-80, 75, 8, fill=0, stroke=1)
    warn = ("CONSULTATION URGENTE — Appelez le 15 (SAMU) immediatement"
            if urgent else
            "Diagnostic indicatif — Consultez un medecin pour confirmation")
    c.setFillColor(brd)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W/2, H-153, warn)
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 10)
    c.drawCentredString(W/2, H-173,
        f"Diagnostic : {data.get('diagnostic','N/A')}  |  "
        f"Confiance : {data.get('confiance',0):.0f}%")

    # Profil patient
    y = H-220
    _titre_section(c, y, "Profil du patient", C_HEALTH)
    y -= 22
    symptomes = data.get("symptomes", [])
    y = _lignes(c, y, [
        ("Age",                 f"{data.get('age','?')} ans"),
        ("Duree des symptomes", data.get("duree_symptomes","N/A")),
        ("Nombre de symptomes", str(len(symptomes))),
        ("Diagnostic probable", data.get("diagnostic","N/A")),
        ("Confiance du modele", f"{data.get('confiance',0):.0f}%"),
    ])

    # Symptomes 2 colonnes
    y -= 20
    _titre_section(c, y, "Symptomes observes", C_HEALTH)
    y -= 22
    ALL_SYM = ["Fièvre","Toux","Fatigue","Maux de tête","Maux de gorge",
               "Nausées","Douleur thoracique","Essoufflement","Diarrhée","Frissons",
               "Perte odorat", "Douleurs musculaires", "Palpitations", "Vertiges"]
    col_x = [50, W//2 + 10]
    row_h = 20
    for idx, sym in enumerate(ALL_SYM):
        cx = col_x[idx % 2]
        cy = y - (idx // 2) * row_h
        present = sym in symptomes
        c.setFillColor(colors.HexColor("#0e1a10") if present else C_BG)
        c.rect(cx-10, cy-5, W//2-30, row_h, fill=1, stroke=0)
        c.setFillColor(C_CYAN if present else C_BORDER)
        c.circle(cx+2, cy+5, 4, fill=1, stroke=0)
        c.setFillColor(C_WHITE if present else C_MUTED)
        c.setFont("Helvetica-Bold" if present else "Helvetica", 9)
        c.drawString(cx+14, cy+2, sym)
        c.setFillColor(C_CYAN if present else C_MUTED)
        c.setFont("Helvetica", 8)
        c.drawRightString(cx + W//2 - 50, cy+2, "Present" if present else "Absent")
    y -= (len(ALL_SYM) // 2 + 1) * row_h + 20

    # Conseils
    if y > 120:
        _titre_section(c, y, "Conseils generaux", C_HEALTH)
        conseils = []
        if urgent:
            conseils.append((C_RED, "Appeler le 15 (SAMU) ou aller aux urgences immediatement."))
        conseils += [
            (C_CYAN,   "Boire au moins 1.5L d'eau par jour et se reposer."),
            (C_ORANGE, "Prendre la temperature toutes les 4h en cas de fievre."),
            (C_PURPLE, "Consulter un medecin si les symptomes persistent ou s'aggravent."),
        ]
        y -= 22
        for i, item in enumerate(conseils):
            col, txt = item
            c.setFillColor(C_SURFACE if i % 2 == 0 else C_BG)
            c.rect(40, y-6, W-80, 22, fill=1, stroke=0)
            c.setFillColor(col)
            c.circle(58, y+6, 4, fill=1, stroke=0)
            c.setFillColor(C_WHITE)
            c.setFont("Helvetica", 9)
            c.drawString(72, y+6, txt)
            y -= 22

    _footer(c)
    c.save()
    return buf.getvalue()
