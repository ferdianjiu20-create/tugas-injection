from flask import Flask, request, render_template, session, redirect, url_for
import sqlite3
import subprocess
import platform
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'kunci_rahasia_lab_sirs' # Wajib untuk menggunakan session

def get_db_connection():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- ALUR 1: CEK LOGIN DI DASHBOARD ---
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login')) # Lempar ke login jika belum ada session
    return render_template('index.html', username=session['username'], role=session['role'])

# --- ALUR 2: PROSES LOGIN & SET SESSION ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db_connection()
    
    # ❌ VULNERABLE SQL INJECTION
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    
    try:
        user = conn.execute(query).fetchone()
        if user:
            # Set sesi pengguna jika berhasil login
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index')) # Masuk ke Dashboard
        else:
            return render_template('login.html', error="Username atau password salah.", query=query, submitted=True)
    except sqlite3.Error as e:
        return render_template('login.html', error=str(e), query=query, submitted=True)
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear() # Hapus semua sesi
    return redirect(url_for('login'))

# --- MODUL LAINNYA ---
@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session: return redirect(url_for('login'))
    
    nama = request.args.get('nama')
    if not nama: return render_template('search.html')
        
    conn = get_db_connection()
    query = f"SELECT * FROM pasien WHERE nama = '{nama}'"
    try:
        pasien = conn.execute(query).fetchall()
        return render_template('search.html', pasien=pasien, query=query, submitted=True)
    except sqlite3.Error as e:
        return render_template('search.html', error=str(e), query=query, submitted=True)
    finally:
        conn.close()

# --- ALUR 3: PEMBATASAN HAK AKSES DOKTER ---
@app.route('/racik', methods=['GET', 'POST'])
def racik():
    if 'username' not in session: return redirect(url_for('login'))
    
    # Cek apakah rolenya Dokter atau Admin (RBAC Sederhana)
    if session.get('role') not in ['Dokter', 'Administrator']:
        return "<h3>Akses Ditolak</h3><p>Hanya Dokter yang dapat mengakses fitur ini.</p><a href='/'>Kembali</a>"

    if request.method == 'GET':
        return render_template('racik.html')
        
    data = {
        'dokter': request.form.get('dokter'),
        'pasien': request.form.get('pasien'),
        'racikan': request.form.get('racikan'),
        'waktu': datetime.now().strftime("%d %B %Y %H:%M")
    }
    return render_template('racik.html', resep=data, submitted=True)

@app.route('/ping', methods=['GET', 'POST'])
def ping():
    if 'username' not in session: return redirect(url_for('login'))
    if request.method == 'GET': return render_template('ping.html')
        
    ip = request.form.get('ip')
    cmd_prefix = "ping -n 1" if platform.system().lower() == "windows" else "ping -c 1"
    command = f"{cmd_prefix} {ip}"
    try:
        output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.STDOUT)
        return render_template('ping.html', output=output, command=command, submitted=True)
    except subprocess.CalledProcessError as e:
        return render_template('ping.html', error=e.output, command=command, submitted=True)
@app.route('/list_pasien')
def list_pasien():
    if 'username' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    # Mengambil seluruh data pasien
    pasien = conn.execute("SELECT * FROM pasien").fetchall()
    conn.close()
    
    return render_template('list_pasien.html', pasien=pasien)

@app.route('/list_dokter')
def list_dokter():
    if 'username' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    # Mengambil hanya user yang memiliki role 'Dokter'
    dokter = conn.execute("SELECT id, username, role FROM users WHERE role = 'Dokter'").fetchall()
    conn.close()
    
    return render_template('list_dokter.html', dokter=dokter)

if __name__ == '__main__':
    app.run(debug=True, port=5000)