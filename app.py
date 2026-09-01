import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Mengambil secret_key dari environment variable hosting, atau fallback ke default saat lokal
app.secret_key = os.environ.get('SECRET_KEY', 'rahasia_super_aman')

# Konfigurasi database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ================= DATABASE MODELS =================
class Pengunjung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

# Model baru untuk Database Barang
class Barang(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    harga = db.Column(db.Integer, nullable=False)
    stok = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Barang {self.nama}>'

# Buat database & tabel secara otomatis saat aplikasi dimulai
with app.app_context():
    db.create_all()

# ================= RUTE PENGUNJUNG =================
@app.route('/', methods=['GET', 'POST'])
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
def edit(id):
    pengunjung = Pengunjung.query.get_or_404(id)
    if request.method == 'POST':
        pengunjung.nama = request.form.get('nama')
        db.session.commit()
        flash('Data pengunjung berhasil diperbarui!', 'info')
        return redirect(url_for('home'))
    
    return render_template('edit.html', pengunjung=pengunjung)

@app.route('/delete/<int:id>')
def delete(id):
    pengunjung = Pengunjung.query.get_or_404(id)
    db.session.delete(pengunjung)
    db.session.commit()
    flash('Data pengunjung berhasil dihapus!', 'danger')
    return redirect(url_for('home'))

# ================= RUTE BARANG (CRUD BARU) =================
# 1. Tampil & Tambah Barang
@app.route('/barang', methods=['GET', 'POST'])
def data_barang():
    if request.method == 'POST':
        nama = request.form.get('nama')
        harga = request.form.get('harga')
        stok = request.form.get('stok')

        if nama and harga and stok:
            barang_baru = Barang(nama=nama, harga=int(harga), stok=int(stok))
            db.session.add(barang_baru)
            db.session.commit()
            flash('Barang berhasil ditambahkan!', 'success')
            return redirect(url_for('data_barang'))

    semua_barang = Barang.query.all()
    return render_template('barang.html', barang_list=semua_barang)

# 2. Edit Barang
@app.route('/barang/edit/<int:id>', methods=['GET', 'POST'])
def edit_barang(id):
    item = Barang.query.get_or_404(id)
    if request.method == 'POST':
        item.nama = request.form.get('nama')
        item.harga = int(request.form.get('harga'))
        item.stok = int(request.form.get('stok'))
        db.session.commit()
        flash('Data barang berhasil diperbarui!', 'info')
        return redirect(url_for('data_barang'))

    return render_template('edit_barang.html', barang=item)

# 3. Hapus Barang
@app.route('/barang/hapus/<int:id>')
def hapus_barang(id):
    item = Barang.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash('Barang berhasil dihapus!', 'danger')
    return redirect(url_for('data_barang'))

# ================= RUTE UTILITAS =================
@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    # Konfigurasi Port & Host dinamis untuk server production
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
    app.run(host='0.0.0.0', port=port, debug=debug_mode)