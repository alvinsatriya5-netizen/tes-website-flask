import sys
import os

# Tambahkan direktori utama (root) ke Python path agar bisa mengimpor app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app