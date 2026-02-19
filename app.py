import streamlit as st
import sqlite3
import hashlib
import secrets
import string
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# ========================
# CONEXÃO BANCO
# ========================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# ========================
# CRIAR TABELAS
# ========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cnpj TEXT,
    email TEXT,
    telefone TEXT,
    status TEXT,
    plano TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    receita REAL,
    impostos REAL,
    custos REAL,
    despesas REAL,
    ebitda REAL,
    lucro_liquido REAL,
    margem_ebitda REAL,
    margem_liquida REAL,
    score INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    email TEXT,
    senha TEXT
)
""")

conn.commit()

# ========================
# FUNÇÕES
# ========================

def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def gerar_senha():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))

def calcular_score(margem):
    if margem >= 20:
        return 90
    elif margem >= 10:
        return 75
    elif margem >= 5:
        return 60
    else:
        return 40

def gerar_pdf(nome, receita, lucro, margem, score):
    file_name = f"relatorio_{nome}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []
    styles = getSampleStyle
