import os
import sys

# Ambil path ke direktori root proyek
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Pastikan direktori root berada di urutan paling depan sys.path
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Impor instance Flask dari app.py
from app import app

# Expose 'app' secara langsung untuk Vercel Serverless Function (WSGI Handler)
app = app

if __name__ == "__main__":
    app.run()