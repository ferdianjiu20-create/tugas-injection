from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import subprocess
import platform
import re
import secrets

app = Flask(__name__)
app.secret_key = "kunci_rahasia_sirs_laboratorium_keamanan"

def init_db():
    conn = sqlite3.connect('hospital.db')
    cursor = conn.cursor()
    # Tabel Users
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,
                        password TEXT,
                        role TEXT)''')
    # Tabel Pasien
    cursor.execute('''CREATE TABLE IF NOT EXISTS pasien (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nama TEXT,
                        diagnosa TEXT,
                        kamar TEXT)''')
    # Tabel Catatan Medis
    cursor.execute('''CREATE TABLE IF NOT EXISTS catatan_medis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        penulis TEXT,
                        pesan TEXT)''')
    
    # Isi Data Dummy jika kosong
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'Administrator')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('dokter_budi', 'doc123', 'Dokter Spesialis')")
        
        cursor.execute("INSERT INTO pasien (nama, diagnosa, kamar) VALUES ('Budi Santoso', 'Hipertensi', 'Bed 302')")
        cursor.execute("INSERT INTO pasien (nama, diagnosa, kamar) VALUES ('Siti Aminah', 'Diabetes Melitus', 'Bed 305')")
        cursor.execute("INSERT INTO pasien (nama, diagnosa, kamar) VALUES ('Ahmad Yani', 'Post Surgery', 'ICU 01')")
        
        cursor.execute("INSERT INTO catatan_medis (penulis, pesan) VALUES ('admin (Administrator)', 'Pasien Budi Santoso | Catatan: Berikan obat amlodipine 5mg.')")
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- RUTE TOGGLE SAKELAR GLOBAL ---
@app.route('/toggle_mode')
def toggle_mode():
    session['secure_mode'] = not session.get('secure_mode', False)
    return redirect(request.referrer or url_for('index'))

# --- 1. MODUL LOGIN (SQL INJECTION) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    executed_query = None
    error = None
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        conn = get_db_connection()
        is_secure = session.get('secure_mode', False)
        
        if is_secure:
            # ✔️ VERSI AMAN: Parameterized Query
            query_template = "SELECT * FROM users WHERE username = ? AND password = ?"
            executed_query = f"SQL Prepared Statement:\nQuery: {query_template}\nParams: ('{username}', '{password}')"
            user = conn.execute(query_template, (username, password)).fetchone()
        else:
            # ❌ VERSI RENTAN: String Concatenation SQLi
            executed_query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
            user = conn.execute(executed_query).fetchone()
            
        conn.close()
        
        if user:
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            error = "Username atau Password salah!"
            
    return render_template('login.html', executed_query=executed_query, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- DASHBOARD UTAMA ---
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

# --- 2. MODUL PENCARIAN PASIEN (SQL INJECTION) ---
@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    nama = request.args.get('nama', '')
    pasien_list = []
    executed_query = None
    
    if nama:
        conn = get_db_connection()
        is_secure = session.get('secure_mode', False)
        
        if is_secure:
            query_template = "SELECT * FROM pasien WHERE nama LIKE ?"
            executed_query = f"SQL Prepared Statement:\nQuery: {query_template}\nParam: '%{nama}%'"
            pasien_list = conn.execute(query_template, ('%' + nama + '%',)).fetchall()
        else:
            executed_query = f"SELECT * FROM pasien WHERE nama = '{nama}'"
            pasien_list = conn.execute(executed_query).fetchall()
            
        conn.close()
    else:
        conn = get_db_connection()
        pasien_list = conn.execute("SELECT * FROM pasien").fetchall()
        conn.close()
        
    return render_template('search.html', pasien_list=pasien_list, executed_query=executed_query, search_key=nama)

# --- 3. MODUL DETAIL PASIEN (UNION-BASED SQL INJECTION) ---
@app.route('/detail_pasien')
def detail_pasien():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    id_pasien = request.args.get('id', '1')
    is_secure = session.get('secure_mode', False)
    conn = get_db_connection()
    pasien = None
    executed_query = None
    
    if is_secure:
        try:
            id_val = int(id_pasien)
            query_template = "SELECT * FROM pasien WHERE id = ?"
            executed_query = f"SQL Prepared Statement:\nQuery: {query_template}\nParam: {id_val}"
            pasien = conn.execute(query_template, (id_val,)).fetchall()
        except (TypeError, ValueError):
            executed_query = f"VALIDASI GAGAL: Input ID '{id_pasien}' bukan Integer!"
    else:
        executed_query = f"SELECT * FROM pasien WHERE id = {id_pasien}"
        try:
            pasien = conn.execute(executed_query).fetchall()
        except sqlite3.Error as e:
            executed_query += f"\n\n[SQL Error]: {e}"
            
    conn.close()
    return render_template('detail_pasien.html', pasien=pasien, executed_query=executed_query, is_secure=is_secure)

# --- 4. MODUL PING JARINGAN (OS COMMAND INJECTION) ---
@app.route('/ping', methods=['GET', 'POST'])
def ping():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    output = None
    executed_command = None
    
    if request.method == 'POST':
        ip = request.form.get('ip', '')
        is_secure = session.get('secure_mode', False)
        
        if is_secure:
            # ✔️ VERSI AMAN: Regex Filter IPv4 Standar
            if not re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip):
                executed_command = f"REGEX VALIDATION FAILED for input: '{ip}'"
                output = "Format IP Address tidak valid! Karakter berbahaya atau gabungan perintah ditolak."
            else:
                param = "-n" if platform.system().lower() == "windows" else "-c"
                command = ["ping", param, "1", ip]
                executed_command = f"Subprocess Exec (Safe List): {command}"
                try:
                    output = subprocess.check_output(command, text=True, stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as e:
                    output = e.output
        else:
            # ❌ VERSI RENTAN: Shell Concatenation (shell=True)
            cmd_prefix = "ping -n 1" if platform.system().lower() == "windows" else "ping -c 1"
            executed_command = f"{cmd_prefix} {ip}"
            try:
                output = subprocess.check_output(executed_command, shell=True, text=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                output = e.output
                
    return render_template('ping.html', output=output, executed_command=executed_command)

# --- 5. MODUL CATATAN MEDIS (STORED XSS & CSRF) ---
@app.route('/catatan_medis', methods=['GET', 'POST'])
def catatan_medis():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    is_secure = session.get('secure_mode', False)
    
    if request.method == 'POST':
        if is_secure:
            # ✔️ VERSI AMAN: Validasi CSRF Token
            form_token = request.form.get('csrf_token')
            session_token = session.get('csrf_token')
            if not form_token or form_token != session_token:
                conn.close()
                return "Peringatan Keamanan: Invalid CSRF Token! Access Denied 403.", 403
                
        pasien_terkait = request.form.get('pasien_terkait', '')
        pesan = request.form.get('pesan', '')
        penulis = f"{session['username']} ({session.get('role', 'User')})"
        
        conn.execute("INSERT INTO catatan_medis (penulis, pesan) VALUES (?, ?)", 
                     (penulis, f"Pasien: {pasien_terkait} | Catatan: {pesan}"))
        conn.commit()
        conn.close()
        return redirect(url_for('catatan_medis'))
        
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
        
    catatan_list = conn.execute("SELECT * FROM catatan_medis ORDER BY id DESC").fetchall()
    conn.close()
    
    return render_template('catatan_medis.html', 
                           catatan_list=catatan_list, 
                           csrf_token=session.get('csrf_token'), 
                           is_secure=is_secure)
# --- MODUL PENCARIAN DOKTER (REFLECTED XSS) ---
@app.route('/search_reflected', methods=['GET'])
def search_reflected():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    query = request.args.get('q', '')
    is_secure = session.get('secure_mode', False)
    
    # Kueri mentah/perintah yang dipantulkan untuk ditampilkan di Live Log
    executed_log = f"URL Query Parameter Received: q = '{query}'"
    
    return render_template('search_reflected.html', 
                           query=query, 
                           is_secure=is_secure, 
                           executed_query=executed_log)
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
