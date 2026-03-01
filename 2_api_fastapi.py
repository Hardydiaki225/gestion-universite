from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from pymongo import MongoClient
from datetime import datetime
from typing import Optional

app = FastAPI(title="Universite API - MySQL to MongoDB", version="1.0.0")

# -----------------------------------------------
# MODIFIE ICI TON MOT DE PASSE SI NECESSAIRE
# -----------------------------------------------
SQL_URL = "mysql+pymysql://root:root@localhost:3306/universite"
MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "universite"

sql_engine = create_engine(SQL_URL)
mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client[MONGO_DB]


@app.get("/")
def root():
    return {"status": "ok", "message": "API Universite operationnelle"}


@app.get("/health")
def health():
    try:
        with sql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        mongo_db.command("ping")
        return {"mysql": "connecte", "mongodb": "connecte"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transfert/etudiants")
def transfert_etudiants():
    with sql_engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT e.*, f.nom AS filiere_nom, f.code AS filiere_code,
                   d.nom AS departement_nom
            FROM etudiants e
            JOIN filieres f ON e.filiere_id = f.id
            JOIN departements d ON f.departement_id = d.id
        """)).mappings().all()

    documents = []
    for r in rows:
        doc = {
            "_id": f"ETU_{r['id']}",
            "matricule": r["matricule"],
            "identite": {
                "nom": r["nom"],
                "prenom": r["prenom"],
                "email": r["email"],
                "telephone": r.get("telephone"),
                "date_naissance": str(r["date_naissance"]) if r.get("date_naissance") else None,
            },
            "scolarite": {
                "filiere": r["filiere_nom"],
                "filiere_code": r["filiere_code"],
                "departement": r["departement_nom"],
                "annee_inscription": r["annee_inscription"],
                "statut": r["statut"],
            },
            "notes": [],
            "synced_at": datetime.utcnow()
        }
        documents.append(doc)

    collection = mongo_db["etudiants"]
    for doc in documents:
        collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    return {"message": f"{len(documents)} etudiants transferes vers MongoDB"}


@app.post("/transfert/cours")
def transfert_cours():
    with sql_engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT c.*, f.nom AS filiere_nom,
                   p.nom AS prof_nom, p.prenom AS prof_prenom,
                   p.grade AS prof_grade, p.specialite AS prof_specialite
            FROM cours c
            JOIN filieres f ON c.filiere_id = f.id
            LEFT JOIN professeurs p ON c.professeur_id = p.id
        """)).mappings().all()

    documents = []
    for r in rows:
        doc = {
            "_id": f"COURS_{r['id']}",
            "code": r["code"],
            "intitule": r["intitule"],
            "credits": r["credits"],
            "volume_horaire": r.get("volume_horaire"),
            "semestre": r.get("semestre"),
            "filiere": r["filiere_nom"],
            "professeur": {
                "nom": r.get("prof_nom"),
                "prenom": r.get("prof_prenom"),
                "grade": r.get("prof_grade"),
                "specialite": r.get("prof_specialite"),
            },
            "synced_at": datetime.utcnow()
        }
        documents.append(doc)

    collection = mongo_db["cours"]
    for doc in documents:
        collection.replace_one({"_id": doc["_id"]}, doc, upsert=True)

    return {"message": f"{len(documents)} cours transferes vers MongoDB"}


@app.post("/transfert/notes")
def transfert_notes():
    with sql_engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT n.*, i.annee_academique, i.statut AS inscription_statut,
                   e.matricule,
                   c.code AS cours_code, c.intitule AS cours_intitule, c.credits
            FROM notes n
            JOIN inscriptions i ON n.inscription_id = i.id
            JOIN etudiants e ON i.etudiant_id = e.id
            JOIN cours c ON i.cours_id = c.id
        """)).mappings().all()

    notes_par_etudiant = {}
    for r in rows:
        key = r["matricule"]
        if key not in notes_par_etudiant:
            notes_par_etudiant[key] = []
        notes_par_etudiant[key].append({
            "cours_code": r["cours_code"],
            "cours_intitule": r["cours_intitule"],
            "credits": r["credits"],
            "annee_academique": r["annee_academique"],
            "note_cc": float(r["note_cc"]) if r["note_cc"] else None,
            "note_exam": float(r["note_exam"]) if r["note_exam"] else None,
            "note_finale": float(r["note_finale"]) if r["note_finale"] else None,
            "mention": r.get("mention"),
            "statut": r["inscription_statut"],
        })

    collection = mongo_db["etudiants"]
    for matricule, notes in notes_par_etudiant.items():
        collection.update_one(
            {"matricule": matricule},
            {"$set": {"notes": notes, "synced_at": datetime.utcnow()}}
        )

    return {"message": f"Notes transferees pour {len(notes_par_etudiant)} etudiants"}


@app.post("/transfert/tout")
def transfert_complet():
    r1 = transfert_cours()
    r2 = transfert_etudiants()
    r3 = transfert_notes()
    return {"cours": r1, "etudiants": r2, "notes": r3}


@app.get("/etudiants")
def get_etudiants(filiere: Optional[str] = None, statut: Optional[str] = None):
    query = {}
    if filiere:
        query["scolarite.filiere_code"] = filiere
    if statut:
        query["scolarite.statut"] = statut
    result = list(mongo_db["etudiants"].find(query, {"_id": 0}))
    return {"total": len(result), "etudiants": result}


@app.get("/etudiants/{matricule}")
def get_etudiant(matricule: str):
    doc = mongo_db["etudiants"].find_one({"matricule": matricule}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Etudiant introuvable")
    return doc


@app.get("/cours")
def get_cours():
    result = list(mongo_db["cours"].find({}, {"_id": 0}))
    return {"total": len(result), "cours": result}


@app.get("/stats/dashboard")
def get_stats():
    pipeline_filieres = [
        {"$group": {"_id": "$scolarite.filiere", "nb_etudiants": {"$sum": 1}}}
    ]
    filieres = list(mongo_db["etudiants"].aggregate(pipeline_filieres))

    pipeline_mentions = [
        {"$unwind": "$notes"},
        {"$group": {"_id": "$notes.mention", "nb": {"$sum": 1}}}
    ]
    mentions = list(mongo_db["etudiants"].aggregate(pipeline_mentions))

    pipeline_moyennes = [
        {"$unwind": "$notes"},
        {"$group": {
            "_id": "$scolarite.filiere",
            "moyenne": {"$avg": "$notes.note_finale"},
            "nb_notes": {"$sum": 1}
        }}
    ]
    moyennes = list(mongo_db["etudiants"].aggregate(pipeline_moyennes))

    return {
        "total_etudiants": mongo_db["etudiants"].count_documents({}),
        "total_cours": mongo_db["cours"].count_documents({}),
        "etudiants_par_filiere": filieres,
        "repartition_mentions": mentions,
        "moyennes_par_filiere": moyennes
    }
