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
import os

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# ==========================
# CONEXÃO BANCO
# ==========================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# ==========================
# RESET INTELIGENTE (ANTI ERRO CLOUD)
# ==========================

def tabela_existe(nome):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (nome,))
    return cursor.fetchone() is not None

def coluna_existe(tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    colunas = [col[1] for col in cursor.fetchall()]
    return coluna in colunas

# Se estrutura antiga existir, apaga tudo
if tabela_existe("empresas"):
    if not coluna_existe("empresas", "plano"):
        cursor.execute("DROP TABLE empresas")
        cursor.execute("DROP TABLE dre")
        cursor.execute("DROP TABLE usuarios")
        conn.commit()

# ==========================
# CRIAR TABELAS
# ==========================

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

# ==========================
# FUNÇÕES
# ==========================

def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def gerar_senha():
    return ''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(10))

def calcular_score(margem_liquida):
    if margem_liquida >= 20:
        return 90
    elif margem_liquida >= 10:
        return 75
    elif margem_liquida >= 5:
        return 60
    else:
        return 40

def gerar_pdf(nome, receita, lucro, margem, score):
    file_name = f"relatorio_{nome}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Relatório Financeiro - {nome}", styles['Heading1']))
    elements.append(Spacer(1, 0.5 * inch))

    elements.append(Paragraph(f"Receita: R$ {receita}", styles['Normal']))
    elements.append(Paragraph(f"Lucro Líquido: R$ {lucro}", styles['Normal']))
    elements.append(Paragraph(f"Margem Líquida: {round(margem,2)}%", styles['Normal']))
    elements.append(Paragraph(f"Score Financeiro: {score}", styles['Normal']))

    doc.build(elements)
    return file_name

# ==========================
# SESSION
# ==========================

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.plano = None

# ==========================
# DIAGNÓSTICO GRATUITO
# ==========================

def cadastro_free():
    st.title("Diagnóstico Financeiro Gratuito")

    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    email = st.text_input("E-mail")
    telefone = st.text_input("Telefone")

    st.subheader("Preencha seu DRE")

    receita = st.number_input("Receita Bruta", min_value=0.0)
    impostos = st.number_input("Impostos", min_value=0.0)
    custos = st.number_input("Custos", min_value=0.0)
    despesas = st.number_input("Despesas Operacionais", min_value=0.0)

    if st.button("Gerar Diagnóstico Gratuito"):

        ebitda = receita - impostos - custos
        lucro = receita - impostos - custos - despesas
        margem_ebitda = (ebitda / receita * 100) if receita > 0 else 0
        margem_liquida = (lucro / receita * 100) if receita > 0 else 0
        score = calcular_score(margem_liquida)

        cursor.
