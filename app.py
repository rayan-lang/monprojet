from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import qrcode
from io import BytesIO
import base64

app = Flask(__name__)
app.secret_key = 'ma_cle_secrete'  # Pour gérer les sessions
DB_FILE = 'sorties.db'
BASE_URL = "https://monprojet-j8sc.onrender.com"

# Mot de passe admin
ADMIN_PASSWORD = "admin123"

# Création des tables si elles n'existent pas
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Table des élèves
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_eleve TEXT UNIQUE,
            horaires TEXT,
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

    # Ajout d'horaires par défaut si la table est vide
    cursor.execute("SELECT COUNT(*) FROM horaires")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO horaires (horaires) VALUES (?)", ("8H, 12H, 14H, 16H",))

    conn.commit()
    conn.close()

init_db()

# Page de connexion admin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            flash("Connexion réussie", "success")
            return redirect(url_for('admin'))
        else:
            flash("Mot de passe incorrect", "danger")
    return render_template('login.html')

# Déconnexion admin
@app.route('/logout')
def logout():
    session.pop('admin', None)
    flash("Déconnexion réussie", "info")
    return redirect(url_for('login'))

# Espace admin protégé
@app.route('/admin')
def admin():
    if not session.get('admin'):
        flash("Accès non autorisé. Veuillez vous connecter.", "danger")
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT nom_eleve, horaires, autorise FROM eleves")
    eleves = cursor.fetchall()

    cursor.execute("SELECT horaires FROM horaires LIMIT 1")
    horaires = cursor.fetchone()[0]

    conn.close()
    return render_template('admin.html', eleves=eleves, horaires=horaires)

# Route de la page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# Génération d'un QR code
@app.route('/generate', methods=['POST'])
def generate_qr():
    nom_eleve = request.form['nom_eleve']

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    qr_data = f"{BASE_URL}/horaires/{nom_eleve}"
    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    conn.close()
    return render_template('qr.html', qr_code=qr_base64, nom_eleve=nom_eleve)

if __name__ == '__main__':
    app.run(debug=True)
