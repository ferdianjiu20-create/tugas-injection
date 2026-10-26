import sqlite3

connection = sqlite3.connect('hospital.db')
cursor = connection.cursor()

# --- TABEL PASIEN ---
cursor.execute('''CREATE TABLE IF NOT EXISTS pasien (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT NOT NULL, umur INTEGER, riwayat_medis TEXT)''')
cursor.execute("DELETE FROM pasien") 

# Menambahkan 8 data pasien
pasien_data = [
    ('Budi Santoso', 45, 'Hipertensi, Diabetes Tipe 2'),
    ('Siti Rahma', 32, 'Asma, Alergi Paracetamol'),
    ('Agus Setiawan', 50, 'Kolesterol Tinggi, Jantung Koroner'),
    ('Rini Yuliana', 28, 'Maag Kronis, Vertigo'),
    ('Joko Pranoto', 60, 'Asam Urat, Radang Sendi'),
    ('Ayu Lestari', 22, 'Anemia Ringan'),
    ('Hendra Gunawan', 35, 'Migrain, Insomnia'),
    ('Dewi Sartika', 41, 'Bronkitis, Alergi Debu')
]
cursor.executemany("INSERT INTO pasien (nama, umur, riwayat_medis) VALUES (?, ?, ?)", pasien_data)

# --- TABEL USERS (DOKTER & ADMIN) ---
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, password TEXT NOT NULL, role TEXT)''')
cursor.execute("DELETE FROM users") 

# Menambahkan Admin dan 5 Dokter
users_data = [
    ('admin', 'admin123', 'Administrator'), 
    ('dr_andi', 'dokter123', 'Dokter'),
    ('dr_sari', 'sari123', 'Dokter'),
    ('dr_bima', 'bima123', 'Dokter'),
    ('dr_lisa', 'lisa123', 'Dokter'),
    ('dr_hendra', 'hendra123', 'Dokter')
]
cursor.executemany("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", users_data)

connection.commit()
connection.close()
print("Database diperbarui: Data Pasien dan Dokter berhasil diperbanyak!")