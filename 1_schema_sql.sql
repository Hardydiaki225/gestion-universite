CREATE DATABASE IF NOT EXISTS universite;
USE universite;
-- ============================================
-- SCHÉMA SQL - Gestion Universitaire
-- ============================================

-- 1. DÉPARTEMENTS & FILIÈRES
CREATE TABLE departements (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE filieres (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    code VARCHAR(10) UNIQUE NOT NULL,
    duree_annees INT NOT NULL,
    departement_id INT REFERENCES departements(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. PROFESSEURS
CREATE TABLE professeurs (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    specialite VARCHAR(100),
    grade VARCHAR(50),  -- Maître assistant, Professeur, etc.
    departement_id INT REFERENCES departements(id),
    date_embauche DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. COURS & MATIÈRES
CREATE TABLE cours (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    intitule VARCHAR(200) NOT NULL,
    credits INT NOT NULL DEFAULT 3,
    volume_horaire INT,  -- en heures
    semestre INT CHECK (semestre BETWEEN 1 AND 10),
    filiere_id INT REFERENCES filieres(id) ON DELETE CASCADE,
    professeur_id INT REFERENCES professeurs(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. ÉTUDIANTS
CREATE TABLE etudiants (
    id SERIAL PRIMARY KEY,
    matricule VARCHAR(20) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    telephone VARCHAR(20),
    date_naissance DATE,
    adresse TEXT,
    nationalite VARCHAR(50),
    filiere_id INT REFERENCES filieres(id),
    annee_inscription INT NOT NULL,
    statut VARCHAR(20) DEFAULT 'actif' CHECK (statut IN ('actif', 'suspendu', 'diplome', 'abandonne')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. INSCRIPTIONS AUX COURS
CREATE TABLE inscriptions (
    id SERIAL PRIMARY KEY,
    etudiant_id INT REFERENCES etudiants(id) ON DELETE CASCADE,
    cours_id INT REFERENCES cours(id) ON DELETE CASCADE,
    annee_academique VARCHAR(10) NOT NULL,  -- ex: "2024-2025"
    statut VARCHAR(20) DEFAULT 'inscrit' CHECK (statut IN ('inscrit', 'validé', 'échoué', 'abandonné')),
    date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(etudiant_id, cours_id, annee_academique)
);

-- 6. NOTES
CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    inscription_id INT REFERENCES inscriptions(id) ON DELETE CASCADE,
    note_cc DECIMAL(4,2) CHECK (note_cc BETWEEN 0 AND 20),   -- Contrôle Continu
    note_exam DECIMAL(4,2) CHECK (note_exam BETWEEN 0 AND 20), -- Examen Final
    note_finale DECIMAL(4,2) GENERATED ALWAYS AS (
        ROUND((note_cc * 0.4 + note_exam * 0.6)::NUMERIC, 2)
    ) STORED,
    mention VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN (note_cc * 0.4 + note_exam * 0.6) >= 16 THEN 'Très Bien'
            WHEN (note_cc * 0.4 + note_exam * 0.6) >= 14 THEN 'Bien'
            WHEN (note_cc * 0.4 + note_exam * 0.6) >= 12 THEN 'Assez Bien'
            WHEN (note_cc * 0.4 + note_exam * 0.6) >= 10 THEN 'Passable'
            ELSE 'Insuffisant'
        END
    ) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- DONNÉES D'EXEMPLE
-- ============================================

INSERT INTO departements (nom, code, description) VALUES
('Informatique', 'INFO', 'Département des sciences informatiques'),
('Mathématiques', 'MATH', 'Département de mathématiques et statistiques'),
('Sciences Économiques', 'ECO', 'Département d'économie et gestion');

INSERT INTO filieres (nom, code, duree_annees, departement_id) VALUES
('Génie Logiciel', 'GL', 3, 1),
('Intelligence Artificielle', 'IA', 3, 1),
('Mathématiques Appliquées', 'MA', 3, 2),
('Finance & Comptabilité', 'FC', 3, 3);

INSERT INTO professeurs (nom, prenom, email, specialite, grade, departement_id, date_embauche) VALUES
('Dupont', 'Jean', 'j.dupont@univ.fr', 'Algorithmique', 'Professeur', 1, '2010-09-01'),
('Martin', 'Sophie', 's.martin@univ.fr', 'Machine Learning', 'Maître de Conférences', 1, '2015-09-01'),
('Bernard', 'Luc', 'l.bernard@univ.fr', 'Analyse', 'Professeur', 2, '2008-09-01'),
('Petit', 'Marie', 'm.petit@univ.fr', 'Économétrie', 'Maître Assistante', 3, '2018-09-01');

INSERT INTO cours (code, intitule, credits, volume_horaire, semestre, filiere_id, professeur_id) VALUES
('GL101', 'Algorithmique & Structures de Données', 4, 60, 1, 1, 1),
('GL102', 'Programmation Orientée Objet', 3, 45, 1, 1, 1),
('IA201', 'Introduction au Machine Learning', 4, 60, 3, 2, 2),
('IA202', 'Deep Learning', 3, 45, 4, 2, 2),
('MA101', 'Analyse Mathématique', 4, 60, 1, 3, 3),
('FC101', 'Comptabilité Générale', 3, 45, 1, 4, 4);

INSERT INTO etudiants (matricule, nom, prenom, email, date_naissance, filiere_id, annee_inscription) VALUES
('ETU001', 'Diallo', 'Amadou', 'a.diallo@etud.fr', '2002-03-15', 1, 2023),
('ETU002', 'Koné', 'Fatima', 'f.kone@etud.fr', '2001-07-22', 1, 2022),
('ETU003', 'Traoré', 'Ibrahim', 'i.traore@etud.fr', '2003-01-10', 2, 2023),
('ETU004', 'Sow', 'Aissatou', 'a.sow@etud.fr', '2002-11-05', 3, 2023),
('ETU005', 'Coulibaly', 'Moussa', 'm.coulibaly@etud.fr', '2001-09-18', 4, 2022);

INSERT INTO inscriptions (etudiant_id, cours_id, annee_academique) VALUES
(1, 1, '2023-2024'), (1, 2, '2023-2024'),
(2, 1, '2023-2024'), (2, 2, '2023-2024'),
(3, 3, '2023-2024'), (3, 4, '2023-2024'),
(4, 5, '2023-2024'),
(5, 6, '2023-2024');

INSERT INTO notes (inscription_id, note_cc, note_exam) VALUES
(1, 14.5, 16.0), (2, 12.0, 13.5),
(3, 16.0, 17.5), (4, 15.0, 14.0),
(5, 11.0, 12.0), (6, 13.5, 15.0),
(7, 18.0, 19.0),
(8, 9.5, 11.0);
