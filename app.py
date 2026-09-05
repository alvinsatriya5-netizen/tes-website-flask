import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Mengambil secret_key dari environment variable hosting, atau fallback ke default saat lokal
app.secret_key = os.environ.get('SECRET_KEY', 'rahasia_super_aman')

# ================= KONFIGURASI DATABASE VERCEL POSTGRES / SQLITE =================
db_url = os.environ.get('POSTGRES_URL') or os.environ.get('STORAGE_URL') or os.environ.get('DATABASE_URL')

# Perbaikan format URI dari postgres:// ke postgresql:// (wajib untuk SQLAlchemy & Vercel)
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Gunakan Vercel Postgres jika ada, jika tidak ada (lokal) fallback ke SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= HELPER WAKTU WIB (GMT+7) =================
def waktu_wib():
    return datetime.utcnow() + timedelta(hours=7)

# ================= DATABASE MODELS =================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' atau 'user'

class Pengunjung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

class Barang(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    harga = db.Column(db.Integer, nullable=False)
    stok = db.Column(db.Float, nullable=False, default=0.0)
    satuan = db.Column(db.String(50), nullable=False, default='pcs')

    def __repr__(self):
        return f'<Barang {self.nama}>'

class RiwayatTransaksi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    barang_id = db.Column(db.Integer, db.ForeignKey('barang.id'), nullable=False)
    tipe = db.Column(db.String(20), nullable=False)
    jumlah = db.Column(db.Float, nullable=False)
    tanggal = db.Column(db.DateTime, default=waktu_wib)
    
    barang = db.relationship('Barang', backref=db.backref('riwayat', lazy=True))

# Buat database & tabel secara otomatis saat aplikasi dimulai, buat akun default jika belum ada
with app.app_context():
    try:
        db.create_all()
        # Membuat akun admin default
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
        # Membuat akun user biasa default
        if not User.query.filter_by(username='user').first():
            normal_user = User(
                username='user',
                password=generate_password_hash('user123'),
                role='user'
            )
            db.session.add(normal_user)
        db.session.commit()
    except Exception as e:
        print("Log DB Create Error:", e)

# ================= DECORATOR HAK AKSES =================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu!', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu!', 'danger')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Akses ditolak! Fitur ini khusus untuk Admin.', 'danger')
            return redirect(url_for('data_barang'))
        return f(*args, **kwargs)
    return decorated_function

# ================= RUTE AUTENTIKASI =================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash(f'Selamat datang, {user.username} ({user.role.capitalize()})!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Username atau password salah!', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda berhasil keluar.', 'info')
    return redirect(url_for('login'))

# ================= RUTE PENGUNJUNG =================
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        nama_input = request.form.get('nama')
        if nama_input:
            pengunjung_baru = Pengunjung(nama=nama_input)
            db.session.add(pengunjung_baru)
            db.session.commit()
            flash('Pengunjung berhasil ditambahkan!', 'success')
            return redirect(url_for('home'))

    semua_pengunjung = Pengunjung.query.all()
    return render_template('index.html', daftar_pengunjung=semua_pengunjung)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit(id):
    pengunjung = Pengunjung.query.get_or_404(id)
    if request.method == 'POST':
        pengunjung.nama = request.form.get('nama')
        db.session.commit()
        flash('Data pengunjung berhasil diperbarui!', 'info')
        return redirect(url_for('home'))
    
    return render_template('edit.html', pengunjung=pengunjung)

@app.route('/delete/<int:id>')
@admin_required
def delete(id):
    pengunjung = Pengunjung.query.get_or_404(id)
    db.session.delete(pengunjung)
    db.session.commit()
    flash('Data pengunjung berhasil dihapus!', 'danger')
    return redirect(url_for('home'))

# ================= RUTE BARANG (CRUD & TRANSAKSI) =================
@app.route('/barang', methods=['GET', 'POST'])
@login_required
def data_barang():
    if request.method == 'POST':
        if session.get('role') != 'admin':
            flash('Akses ditolak! Hanya Admin yang dapat menambah barang.', 'danger')
            return redirect(url_for('data_barang'))

        nama = request.form.get('nama')
        harga = request.form.get('harga')
        stok = request.form.get('stok')
        satuan = request.form.get('satuan', 'pcs')

        if nama and harga and stok and satuan:
            barang_baru = Barang(nama=nama, harga=int(harga), stok=float(stok), satuan=satuan)
            db.session.add(barang_baru)
            db.session.commit()
            flash('Barang berhasil ditambahkan!', 'success')
            return redirect(url_for('data_barang'))

    semua_barang = Barang.query.all()
    riwayat_list = RiwayatTransaksi.query.order_by(RiwayatTransaksi.tanggal.desc()).all()

    return render_template('barang.html', barang_list=semua_barang, riwayat_list=riwayat_list)

@app.route('/barang/transaksi', methods=['POST'])
@admin_required
def transaksi_barang():
    barang_id = request.form.get('barang_id')
    tipe = request.form.get('tipe')
    jumlah_input = request.form.get('jumlah')

    if barang_id and tipe and jumlah_input:
        jumlah = float(jumlah_input)
        item = Barang.query.get_or_404(int(barang_id))

        if tipe == 'Masuk':
            item.stok += jumlah
            flash(f'Stok {item.nama} berhasil ditambah {jumlah} {item.satuan}!', 'success')
        elif tipe == 'Keluar':
            if item.stok >= jumlah:
                item.stok -= jumlah
                flash(f'Stok {item.nama} berhasil dikurangi {jumlah} {item.satuan}!', 'info')
            else:
                flash(f'Gagal! Stok {item.nama} tidak mencukupi (Tersisa: {item.stok} {item.satuan}).', 'danger')
                return redirect(url_for('data_barang'))

        log = RiwayatTransaksi(barang_id=item.id, tipe=tipe, jumlah=jumlah)
        db.session.add(log)
        db.session.commit()

    return redirect(url_for('data_barang'))

@app.route('/barang/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_barang(id):
    item = Barang.query.get_or_404(id)
    if request.method == 'POST':
        item.nama = request.form.get('nama')
        item.harga = int(request.form.get('harga'))
        item.stok = float(request.form.get('stok'))
        item.satuan = request.form.get('satuan')
        db.session.commit()
        flash('Data barang berhasil diperbarui!', 'info')
        return redirect(url_for('data_barang'))

    return render_template('edit_barang.html', barang=item)

@app.route('/barang/hapus/<int:id>')
@admin_required
def hapus_barang(id):
    item = Barang.query.get_or_404(id)
    RiwayatTransaksi.query.filter_by(barang_id=item.id).delete()
    db.session.delete(item)
    db.session.commit()
    flash('Barang dan riwayat transaksinya berhasil dihapus!', 'danger')
    return redirect(url_for('data_barang'))

# ================= RUTE UTILITAS =================
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
    app.run(host='0.0.0.0', port=port, debug=debug_mode)