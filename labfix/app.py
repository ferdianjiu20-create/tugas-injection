from flask import Flask, request, render_template, session, redirect, url_for
import sqlite3
import subprocess
import platform
from datetime import datetime
import re

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
    
    # ✅ AMAN: Menggunakan Parameterized Query (Prepared Statements)
    # Tanda '?' berfungsi sebagai placeholder yang aman dari SQL Injection
    query = "SELECT * FROM users WHERE username = ? AND password = ?"
    
    try:
        # Masukkan variabel username dan password ke dalam tuple pada parameter kedua execute()
        user = conn.execute(query, (username, password)).fetchone()
        
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
    # ✅ AMAN: Menggunakan Parameterized Query dengan operator LIKE
    # Tanda '?' adalah placeholder aman, dan simbol '%' digabung di dalam tuple parameter
    query = "SELECT * FROM pasien WHERE nama LIKE ?"
    
    try:
        # '%'+ nama + '%' membuat pencarian fleksibel (mencari nama yang mengandung kata tersebut)
        pasien = conn.execute(query, ('%' + nama + '%',)).fetchall()
        
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
    
    # ✅ VALIDASI INPUT: Pastikan hanya berisi karakter yang diizinkan untuk IP/Hostname 
    # (Alfanumerik, titik, dan tanda hubung/strip) guna mencegah injeksi simbol terminal
    if not re.match(r"^[a-zA-Z0-9.-]+$", ip):
        return render_template('ping.html', error="Input tidak valid! Karakter khusus tidak diizinkan.", command=ip, submitted=True)

    # ✅ MENENTUKAN PERINTAH DALAM BENTUK LIST (Bukan String)
    # Ini wajib agar Python tidak menggunakan shell
    cmd_prefix = ["ping", "-n", "1"] if platform.system().lower() == "windows" else ["ping", "-c", "1"]
    
    # Menggabungkan list command dengan input IP yang sudah divalidasi
    command_list = cmd_prefix + [ip]

    try:
        # ✅ AMAN: Menggunakan shell=False (default) dan timeout untuk mencegah gantung (hanging)
        output = subprocess.check_output(command_list, text=True, stderr=subprocess.STDOUT, timeout=5)
        
        # Untuk ditampilkan di UI (dijadikan string kembali agar rapi)
        command_display = " ".join(command_list)
        return render_template('ping.html', output=output, command=command_display, submitted=True)
        
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        error_output = e.output if hasattr(e, 'output') else str(e)
        command_display = " ".join(command_list)
        return render_template('ping.html', error=error_output, command=command_display, submitted=True)
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