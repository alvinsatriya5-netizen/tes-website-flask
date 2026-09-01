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

# Tabel Database
class Pengunjung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)

# Buat database & tabel secara otomatis saat aplikasi dimulai
with app.app_context():
    db.create_all()

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

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    # Konfigurasi Port & Host dinamis untuk server production
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1']
    app.run(host='0.0.0.0', port=port, debug=debug_mode)