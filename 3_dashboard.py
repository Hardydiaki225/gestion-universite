"""
==============================================
DASHBOARD STREAMLIT - Gestion Universitaire
Données depuis MongoDB
==============================================

Installation :
    pip install streamlit pymongo pandas plotly

Lancement :
    streamlit run 3_dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import os

# -----------------------------------------------
# CONFIGURATION
# -----------------------------------------------
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "universite")

st.set_page_config(
    page_title="Université - Dashboard",
    page_icon="🎓",
    layout="wide"
)

# -----------------------------------------------
# CONNEXION MONGODB
# -----------------------------------------------
@st.cache_resource
def get_mongo():
    client = MongoClient(MONGO_URL)
    return client[MONGO_DB]

db = get_mongo()


# -----------------------------------------------
# CHARGEMENT DES DONNÉES
# -----------------------------------------------
@st.cache_data(ttl=60)
def load_etudiants():
    docs = list(db["etudiants"].find({}, {"_id": 0}))
    return docs

@st.cache_data(ttl=60)
def load_cours():
    docs = list(db["cours"].find({}, {"_id": 0}))
    return pd.DataFrame(docs) if docs else pd.DataFrame()

etudiants_raw = load_etudiants()
df_cours = load_cours()

# Transformer les étudiants en DataFrame plat
rows = []
for e in etudiants_raw:
    base = {
        "matricule": e.get("matricule"),
        "nom": e.get("identite", {}).get("nom"),
        "prenom": e.get("identite", {}).get("prenom"),
        "email": e.get("identite", {}).get("email"),
        "filiere": e.get("scolarite", {}).get("filiere"),
        "filiere_code": e.get("scolarite", {}).get("filiere_code"),
        "departement": e.get("scolarite", {}).get("departement"),
        "annee_inscription": e.get("scolarite", {}).get("annee_inscription"),
        "statut": e.get("scolarite", {}).get("statut"),
    }
    rows.append(base)
df_etudiants = pd.DataFrame(rows)

# DataFrame notes
notes_rows = []
for e in etudiants_raw:
    for n in e.get("notes", []):
        notes_rows.append({
            "matricule": e.get("matricule"),
            "nom_complet": f"{e.get('identite',{}).get('prenom','')} {e.get('identite',{}).get('nom','')}",
            "filiere": e.get("scolarite", {}).get("filiere"),
            **n
        })
df_notes = pd.DataFrame(notes_rows)


# -----------------------------------------------
# INTERFACE
# -----------------------------------------------
st.title("🎓 Tableau de Bord — Gestion Universitaire")
st.markdown("---")

# -----------------------------------------------
# MÉTRIQUES GLOBALES
# -----------------------------------------------
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("👨‍🎓 Total Étudiants", len(df_etudiants))
with col2:
    st.metric("📚 Total Cours", len(df_cours))
with col3:
    actifs = len(df_etudiants[df_etudiants["statut"] == "actif"]) if not df_etudiants.empty else 0
    st.metric("✅ Étudiants Actifs", actifs)
with col4:
    if not df_notes.empty and "note_finale" in df_notes.columns:
        moy_gen = round(df_notes["note_finale"].mean(), 2)
        st.metric("📊 Moyenne Générale", f"{moy_gen}/20")
    else:
        st.metric("📊 Moyenne Générale", "N/A")

st.markdown("---")

# -----------------------------------------------
# LIGNE 1 : GRAPHIQUES GÉNÉRAUX
# -----------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("👨‍🎓 Étudiants par Filière")
    if not df_etudiants.empty:
        df_fil = df_etudiants.groupby("filiere").size().reset_index(name="nb_etudiants")
        fig = px.pie(df_fil, names="filiere", values="nb_etudiants",
                     color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible")

with col2:
    st.subheader("🏅 Répartition des Mentions")
    if not df_notes.empty and "mention" in df_notes.columns:
        df_mention = df_notes.groupby("mention").size().reset_index(name="nb")
        ordre = ["Très Bien", "Bien", "Assez Bien", "Passable", "Insuffisant"]
        df_mention["mention"] = pd.Categorical(df_mention["mention"], categories=ordre, ordered=True)
        df_mention = df_mention.sort_values("mention")
        colors = ["#2ecc71", "#3498db", "#f39c12", "#e67e22", "#e74c3c"]
        fig = px.bar(df_mention, x="mention", y="nb",
                     color="mention",
                     color_discrete_sequence=colors)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible")

# -----------------------------------------------
# LIGNE 2 : MOYENNES & ÉVOLUTION
# -----------------------------------------------
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Moyenne par Filière")
    if not df_notes.empty and "note_finale" in df_notes.columns:
        df_moy = df_notes.groupby("filiere")["note_finale"].mean().reset_index()
        df_moy.columns = ["Filière", "Moyenne"]
        df_moy["Moyenne"] = df_moy["Moyenne"].round(2)
        fig = px.bar(df_moy, x="Filière", y="Moyenne",
                     color="Moyenne",
                     color_continuous_scale="RdYlGn",
                     range_y=[0, 20])
        fig.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Seuil de passage")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("📈 Étudiants par Année d'Inscription")
    if not df_etudiants.empty and "annee_inscription" in df_etudiants.columns:
        df_ann = df_etudiants.groupby("annee_inscription").size().reset_index(name="nb")
        fig = px.line(df_ann, x="annee_inscription", y="nb",
                      markers=True, line_shape="spline")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------
# LIGNE 3 : TABLEAUX DÉTAILLÉS
# -----------------------------------------------
st.markdown("---")
st.subheader("🔍 Exploration des Données")

tab1, tab2, tab3 = st.tabs(["👨‍🎓 Étudiants", "📚 Cours", "📝 Notes"])

with tab1:
    if not df_etudiants.empty:
        filiere_filter = st.selectbox("Filtrer par filière", ["Toutes"] + sorted(df_etudiants["filiere"].dropna().unique().tolist()))
        df_show = df_etudiants if filiere_filter == "Toutes" else df_etudiants[df_etudiants["filiere"] == filiere_filter]
        st.dataframe(df_show.reset_index(drop=True), use_container_width=True)
        st.caption(f"{len(df_show)} étudiant(s) affiché(s)")

with tab2:
    if not df_cours.empty:
        st.dataframe(df_cours.drop(columns=["professeur"], errors="ignore"), use_container_width=True)
    else:
        st.info("Aucun cours trouvé")

with tab3:
    if not df_notes.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            filiere_n = st.selectbox("Filière", ["Toutes"] + sorted(df_notes["filiere"].dropna().unique().tolist()), key="filiere_notes")
        with col_b:
            mention_n = st.selectbox("Mention", ["Toutes"] + sorted(df_notes["mention"].dropna().unique().tolist()), key="mention_notes")

        df_n = df_notes.copy()
        if filiere_n != "Toutes":
            df_n = df_n[df_n["filiere"] == filiere_n]
        if mention_n != "Toutes":
            df_n = df_n[df_n["mention"] == mention_n]

        cols_afficher = ["nom_complet", "filiere", "cours_code", "cours_intitule", "note_cc", "note_exam", "note_finale", "mention"]
        cols_existantes = [c for c in cols_afficher if c in df_n.columns]
        st.dataframe(df_n[cols_existantes].reset_index(drop=True), use_container_width=True)
        st.caption(f"{len(df_n)} note(s) affichée(s)")

# -----------------------------------------------
# FOOTER
# -----------------------------------------------
st.markdown("---")
st.markdown(
    "<center><small>🎓 Dashboard Université — Données MongoDB | Développé avec FastAPI + Streamlit</small></center>",
    unsafe_allow_html=True
)
