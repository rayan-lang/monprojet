from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = 'ma_cle_secrete'
DB_FILE = 'sorties.db'

# URL de base pour l'application déployée sur Render
BASE_URL = "https://monprojet-j8sc.onrender.com"  # Remplace par ton URL Render

# Création des tables si elles n'existent pas
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Table historique des sorties
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historique (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_eleve TEXT,
            heure_sortie TEXT,
            date TEXT
        )
    ''')

    # Table des élèves
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_eleve TEXT UNIQUE,
            autorise INTEGER DEFAULT 0
        )
    ''')

    # Table des horaires
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS horaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            horaires TEXT
        )
    ''')

    # Ajout des horaires par défaut si la table est vide
    cursor.execute("SELECT COUNT(*) FROM horaires")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO horaires (horaires) VALUES (?)", ("8H, 12H, 14H, 16H",))

    conn.commit()
    conn.close()

init_db()

# Page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# Génération de QR code avec redirection vers la page des horaires de l'élève
@app.route('/generate', methods=['POST'])
def generate_qr():
    nom_eleve = request.form['nom_eleve']

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Ajouter l'élève dans la table eleves s'il n'existe pas
    cursor.execute("INSERT OR IGNORE INTO eleves (nom_eleve) VALUES (?)", (nom_eleve,))
    conn.commit()

    # URL de la page des horaires
    qr_data = f"{BASE_URL}/horaires/{nom_eleve}"

    # Générer le QR code avec l'URL complète
    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    conn.close()
    return render_template('qr.html', qr_code=qr_base64, nom_eleve=nom_eleve)

# Historique des sorties
@app.route('/historique')
def historique():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT nom_eleve, heure_sortie, date FROM historique")
    sorties = cursor.fetchall()
    conn.close()
    return render_template('historique.html', sorties=sorties)

# Espace admin
@app.route('/admin')
def admin():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Récupérer les élèves
    cursor.execute("SELECT nom_eleve, autorise FROM eleves")
    eleves = cursor.fetchall()

    # Récupérer les horaires dynamiques
    cursor.execute("SELECT horaires FROM horaires LIMIT 1")
    horaires = cursor.fetchone()[0]

    conn.close()
    return render_template('admin.html', eleves=eleves, horaires=horaires)

# Mise à jour des permissions d'un élève
@app.route('/update_permission', methods=['POST'])
def update_permission():
    nom_eleve = request.form['nom_eleve']
    autorise = 1 if 'autorise' in request.form else 0

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE eleves SET autorise = ? WHERE nom_eleve = ?", (autorise, nom_eleve))
    conn.commit()
    conn.close()
    flash(f"Permission mise à jour pour {nom_eleve}", "success")
    return redirect(url_for('admin'))

# Mise à jour des horaires
@app.route('/update_horaires', methods=['POST'])
def update_horaires():
    nouveaux_horaires = request.form['horaires']

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE horaires SET horaires = ? WHERE id = 1", (nouveaux_horaires,))
    conn.commit()
    conn.close()

    flash('Les horaires ont été mis à jour avec succès.', 'success')
    return redirect(url_for('admin'))

# Page des horaires d'un élève (accessible via le QR code)
@app.route('/horaires/<nom_eleve>')
def horaires_eleve(nom_eleve):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Récupérer les horaires dynamiques
    cursor.execute("SELECT horaires FROM horaires LIMIT 1")
    horaires = cursor.fetchone()

    if horaires:
        horaires = horaires[0]

    conn.close()
    return render_template('horaires.html', nom_eleve=nom_eleve, horaires=horaires)

if __name__ == '__main__':
    print("Le serveur Flask démarre...")
    app.run(debug=True)
