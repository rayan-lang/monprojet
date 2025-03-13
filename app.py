import os
import sqlite3
import qrcode
from io import BytesIO
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'ma_cle_secrete'  # Pour les sessions
DB_FILE = 'sorties.db'
BASE_URL = "https://monprojet-j8sc.onrender.com"
UPLOAD_FOLDER = 'static/photos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Identifiants admin
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# Mise à jour de la base de données
def update_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(eleves)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'photo' not in columns:
        cursor.execute("ALTER TABLE eleves ADD COLUMN photo TEXT")
    if 'emploi_du_temps' not in columns:
        cursor.execute("ALTER TABLE eleves ADD COLUMN emploi_du_temps TEXT")

    conn.commit()
    conn.close()


update_db()


# Redirection de la page principale vers la connexion
@app.route('/')
def index():
    return redirect(url_for('login'))


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
    cursor.execute("SELECT nom_eleve, photo, emploi_du_temps FROM eleves")
    eleves = cursor.fetchall()
    conn.close()
    return render_template('admin.html', eleves=eleves)


# Ajout d'un élève
@app.route('/add_eleve', methods=['POST'])
def add_eleve():
    nom_eleve = request.form['nom_eleve']

    # Récupération des jours de l'emploi du temps
    emploi_du_temps = {
        "lundi": request.form.get('lundi'),
        "mardi": request.form.get('mardi'),
        "mercredi": request.form.get('mercredi'),
        "jeudi": request.form.get('jeudi'),
        "vendredi": request.form.get('vendredi')
    }

    # Convertir l'emploi du temps en chaîne JSON pour le stocker dans la base de données
    emploi_du_temps_str = str(emploi_du_temps)  # Vous pouvez aussi utiliser json.dumps() si nécessaire

    # Gestion de la photo de l'élève
    photo = request.files['photo']
    photo_path = None
    if photo and photo.filename != '':
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)

    # Connexion à la base de données et ajout de l'élève
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO eleves (nom_eleve, photo, emploi_du_temps) VALUES (?, ?, ?)",
                       (nom_eleve, photo_path, emploi_du_temps_str))
        conn.commit()
        flash(f"L'élève {nom_eleve} a été ajouté avec succès.", "success")
    except sqlite3.IntegrityError:
        flash(f"L'élève {nom_eleve} existe déjà.", "danger")

    conn.close()
    return redirect(url_for('admin'))


# Suppression d'un élève
@app.route('/delete_eleve/<nom_eleve>', methods=['POST'])
def delete_eleve(nom_eleve):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM eleves WHERE nom_eleve = ?", (nom_eleve,))
    conn.commit()
    conn.close()
    flash(f"L'élève {nom_eleve} a été supprimé.", "info")
    return redirect(url_for('admin'))


if __name__ == '__main__':
    print("🚀 Le serveur Flask démarre...")
    app.run(debug=True)
