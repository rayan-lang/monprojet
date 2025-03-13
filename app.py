from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = 'ma_cle_secrete'  # Pour les sessions
DB_FILE = 'sorties.db'
BASE_URL = "https://monprojet-j8sc.onrender.com"

# Identifiants admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

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

# Page de connexion
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin'] = True
            flash("Connexion réussie", "success")
            return redirect(url_for('admin'))
        else:
            flash("Identifiant ou mot de passe incorrect", "danger")

    return render_template('login.html')

# Déconnexion
@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Déconnexion réussie", "info")
    return redirect(url_for('login'))

# Espace admin sécurisé
@app.route('/admin')
def admin():
    if not session.get('admin'):
        flash("Accès non autorisé. Veuillez vous connecter.", "danger")
        return redirect(url_for('login'))

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

# Page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# Génération de QR code
@app.route('/generate', methods=['POST'])
def generate_qr():
    nom_eleve = request.form['nom_eleve']

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO eleves (nom_eleve) VALUES (?)", (nom_eleve,))
    conn.commit()

    qr_data = f"{BASE_URL}/horaires/{nom_eleve}"

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

# Page des horaires d'un élève
@app.route('/horaires/<nom_eleve>')
def horaires_eleve(nom_eleve):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT horaires FROM horaires LIMIT 1")
    horaires = cursor.fetchone()

    if horaires:
        horaires = horaires[0]

    conn.close()
    return render_template('horaires.html', nom_eleve=nom_eleve, horaires=horaires)

if __name__ == '__main__':
    print("🚀 Le serveur Flask démarre...")
    app.run(debug=True)
