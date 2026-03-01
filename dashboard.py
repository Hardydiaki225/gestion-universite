import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from pymongo import MongoClient

# -----------------------------------------------
# CONFIGURATION
# -----------------------------------------------
API_URL = "http://localhost:8000"
MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "universite"

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
# SESSION STATE
# -----------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "etudiant" not in st.session_state:
    st.session_state.etudiant = None
if "page" not in st.session_state:
    st.session_state.page = "login"


# -----------------------------------------------
# PAGE LOGIN
# -----------------------------------------------
def page_login():
    st.markdown("<h1 style='text-align:center;'>🎓 Université</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:gray;'>Connexion à votre espace étudiant</h3>", unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.subheader("🔐 Se connecter")
            email = st.text_input("Email", placeholder="votre.email@etud.fr")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            submit = st.form_submit_button("Se connecter", use_container_width=True)

            if submit:
                if not email or not password:
                    st.error("Veuillez remplir tous les champs.")
                else:
                    try:
                        response = requests.post(f"{API_URL}/auth/login", json={
                            "email": email,
                            "mot_de_passe": password
                        })
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.logged_in = True
                            st.session_state.etudiant = data
                            st.session_state.page = "dashboard"
                            st.success(f"Bienvenue {data['nom']} !")
                            st.rerun()
                        else:
                            st.error(response.json().get("detail", "Erreur de connexion."))
                    except Exception as e:
                        st.error(f"Impossible de contacter l'API : {e}")

        st.markdown("---")
        st.markdown("<center>Pas encore de compte ?</center>", unsafe_allow_html=True)
        if st.button("📝 S'inscrire", use_container_width=True):
            st.session_state.page = "inscription"
            st.rerun()


# -----------------------------------------------
# PAGE INSCRIPTION
# -----------------------------------------------
def page_inscription():
    st.markdown("<h1 style='text-align:center;'>🎓 Université</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center; color:gray;'>Créer votre compte étudiant</h3>", unsafe_allow_html=True)
    st.markdown("---")

    # Charger les filières depuis l'API
    try:
        filieres_resp = requests.get(f"{API_URL}/filieres")
        filieres = filieres_resp.json()
        filiere_options = {f["nom"]: f["id"] for f in filieres}
    except:
        st.error("Impossible de charger les filières. Vérifiez que l'API est lancée.")
        if st.button("⬅ Retour"):
            st.session_state.page = "login"
            st.rerun()
        return

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("inscription_form"):
            st.subheader("📝 Formulaire d'inscription")

            col_a, col_b = st.columns(2)
            with col_a:
                nom = st.text_input("Nom *", placeholder="Ex: Diallo")
            with col_b:
                prenom = st.text_input("Prénom *", placeholder="Ex: Amadou")

            email = st.text_input("Email *", placeholder="votre.email@etud.fr")

            col_c, col_d = st.columns(2)
            with col_c:
                password = st.text_input("Mot de passe *", type="password", placeholder="Min. 6 caractères")
            with col_d:
                confirm_pwd = st.text_input("Confirmer le mot de passe *", type="password")

            filiere_nom = st.selectbox("Filière *", list(filiere_options.keys()))
            annee = st.number_input("Année d'inscription *", min_value=2000, max_value=2030, value=2024)

            st.markdown("##### Informations optionnelles")
            col_e, col_f = st.columns(2)
            with col_e:
                telephone = st.text_input("Téléphone", placeholder="Ex: +225 0700000000")
                nationalite = st.text_input("Nationalité", placeholder="Ex: Ivoirienne")
            with col_f:
                date_naissance = st.date_input("Date de naissance", value=None)

            submit = st.form_submit_button("Créer mon compte", use_container_width=True)

            if submit:
                if not all([nom, prenom, email, password, confirm_pwd]):
                    st.error("Veuillez remplir tous les champs obligatoires (*).")
                elif password != confirm_pwd:
                    st.error("Les mots de passe ne correspondent pas.")
                elif len(password) < 6:
                    st.error("Le mot de passe doit contenir au moins 6 caractères.")
                else:
                    try:
                        payload = {
                            "nom": nom,
                            "prenom": prenom,
                            "email": email,
                            "mot_de_passe": password,
                            "telephone": telephone if telephone else None,
                            "date_naissance": str(date_naissance) if date_naissance else None,
                            "nationalite": nationalite if nationalite else None,
                            "filiere_id": filiere_options[filiere_nom],
                            "annee_inscription": annee,
                        }
                        response = requests.post(f"{API_URL}/auth/inscription", json=payload)
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"Compte créé avec succès ! Votre matricule : **{data['matricule']}**")
                            st.info("Vous pouvez maintenant vous connecter.")
                        else:
                            st.error(response.json().get("detail", "Erreur lors de l'inscription."))
                    except Exception as e:
                        st.error(f"Erreur : {e}")

        st.markdown("---")
        if st.button("⬅ Retour à la connexion", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# -----------------------------------------------
# PAGE DASHBOARD
# -----------------------------------------------
def page_dashboard():
    etudiant = st.session_state.etudiant

    # Barre latérale
    with st.sidebar:
        st.markdown(f"### 👤 {etudiant['nom']}")
        st.markdown(f"📧 {etudiant['email']}")
        st.markdown(f"🎓 {etudiant['filiere']}")
        st.markdown(f"🪪 {etudiant['matricule']}")
        st.markdown("---")
        if st.button("🚪 Se déconnecter", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.etudiant = None
            st.session_state.page = "login"
            st.rerun()

    # Titre
    st.title("🎓 Tableau de Bord — Gestion Universitaire")
    st.markdown("---")

    # Charger données MongoDB
    @st.cache_data(ttl=60)
    def load_etudiants():
        return list(db["etudiants"].find({}, {"_id": 0}))

    @st.cache_data(ttl=60)
    def load_cours():
        docs = list(db["cours"].find({}, {"_id": 0}))
        return pd.DataFrame(docs) if docs else pd.DataFrame()

    etudiants_raw = load_etudiants()
    df_cours = load_cours()

    rows = []
    for e in etudiants_raw:
        rows.append({
            "matricule": e.get("matricule"),
            "nom": e.get("identite", {}).get("nom"),
            "prenom": e.get("identite", {}).get("prenom"),
            "email": e.get("identite", {}).get("email"),
            "filiere": e.get("scolarite", {}).get("filiere"),
            "filiere_code": e.get("scolarite", {}).get("filiere_code"),
            "departement": e.get("scolarite", {}).get("departement"),
            "annee_inscription": e.get("scolarite", {}).get("annee_inscription"),
            "statut": e.get("scolarite", {}).get("statut"),
        })
    df_etudiants = pd.DataFrame(rows)

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

    # Métriques
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
            moy = round(df_notes["note_finale"].mean(), 2)
            st.metric("📊 Moyenne Générale", f"{moy}/20")
        else:
            st.metric("📊 Moyenne Générale", "N/A")

    st.markdown("---")

    # Graphiques
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👨‍🎓 Étudiants par Filière")
        if not df_etudiants.empty:
            df_fil = df_etudiants.groupby("filiere").size().reset_index(name="nb_etudiants")
            fig = px.pie(df_fil, names="filiere", values="nb_etudiants",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🏅 Répartition des Mentions")
        if not df_notes.empty and "mention" in df_notes.columns:
            df_mention = df_notes.groupby("mention").size().reset_index(name="nb")
            fig = px.bar(df_mention, x="mention", y="nb",
                         color="mention",
                         color_discrete_sequence=["#2ecc71","#3498db","#f39c12","#e67e22","#e74c3c"])
            st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Moyenne par Filière")
        if not df_notes.empty and "note_finale" in df_notes.columns:
            df_moy = df_notes.groupby("filiere")["note_finale"].mean().reset_index()
            df_moy.columns = ["Filière", "Moyenne"]
            df_moy["Moyenne"] = df_moy["Moyenne"].round(2)
            fig = px.bar(df_moy, x="Filière", y="Moyenne", color="Moyenne",
                         color_continuous_scale="RdYlGn", range_y=[0, 20])
            fig.add_hline(y=10, line_dash="dash", line_color="red", annotation_text="Seuil de passage")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📈 Étudiants par Année d'Inscription")
        if not df_etudiants.empty:
            df_ann = df_etudiants.groupby("annee_inscription").size().reset_index(name="nb")
            fig = px.line(df_ann, x="annee_inscription", y="nb", markers=True)
            st.plotly_chart(fig, use_container_width=True)

    # Tableaux
    st.markdown("---")
    st.subheader("🔍 Exploration des Données")
    tab1, tab2, tab3 = st.tabs(["👨‍🎓 Étudiants", "📚 Cours", "📝 Notes"])

    with tab1:
        if not df_etudiants.empty:
            filiere_filter = st.selectbox("Filtrer par filière", ["Toutes"] + sorted(df_etudiants["filiere"].dropna().unique().tolist()))
            df_show = df_etudiants if filiere_filter == "Toutes" else df_etudiants[df_etudiants["filiere"] == filiere_filter]
            st.dataframe(df_show.reset_index(drop=True), use_container_width=True)

    with tab2:
        if not df_cours.empty:
            st.dataframe(df_cours.drop(columns=["professeur"], errors="ignore"), use_container_width=True)

    with tab3:
        if not df_notes.empty:
            col_a, col_b = st.columns(2)
            with col_a:
                fn = st.selectbox("Filière", ["Toutes"] + sorted(df_notes["filiere"].dropna().unique().tolist()))
            with col_b:
                mn = st.selectbox("Mention", ["Toutes"] + sorted(df_notes["mention"].dropna().unique().tolist()))
            df_n = df_notes.copy()
            if fn != "Toutes": df_n = df_n[df_n["filiere"] == fn]
            if mn != "Toutes": df_n = df_n[df_n["mention"] == mn]
            cols = [c for c in ["nom_complet","filiere","cours_code","cours_intitule","note_cc","note_exam","note_finale","mention"] if c in df_n.columns]
            st.dataframe(df_n[cols].reset_index(drop=True), use_container_width=True)

    st.markdown("---")
    st.markdown("<center><small>🎓 Dashboard Université — Données MongoDB</small></center>", unsafe_allow_html=True)


# -----------------------------------------------
# ROUTEUR PRINCIPAL
# -----------------------------------------------
if st.session_state.logged_in:
    page_dashboard()
elif st.session_state.page == "inscription":
    page_inscription()
else:
    page_login()
