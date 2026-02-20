import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Motor Financeiro SaaS", layout="wide")

# =============================
# BANCO DE DADOS
# =============================
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# -------- TABELAS --------
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT UNIQUE,
    senha TEXT,
    plano TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    nome_empresa TEXT,
    cnpj TEXT,
    cidade TEXT,
    estado TEXT,
    data_criacao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    receita REAL,
    custos REAL,
    despesas REAL,
    impostos REAL,
    data TEXT
)
""")

conn.commit()

# =============================
# CRIAR ADMIN AUTOMÁTICO
# =============================
cursor.execute("SELECT * FROM usuarios WHERE email='admin@motorfinanceiro.com'")
admin_existe = cursor.fetchone()

if not admin_existe:
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, plano) VALUES (?, ?, ?, ?)",
        (
            "Administrador",
            "admin@motorfinanceiro.com",
            hashlib.sha256("123456".encode()).hexdigest(),
            "admin"
        )
    )
    conn.commit()

# =============================
# FUNÇÕES
# =============================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(nome, email, senha):
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, plano) VALUES (?, ?, ?, ?)",
            (nome, email, hash_senha(senha), "pendente")
        )
        conn.commit()
        return True
    except:
        return False

def autenticar(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email=? AND senha=?",
        (email, hash_senha(senha))
    )
    return cursor.fetchone()

# =============================
# SESSION
# =============================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# =============================
# LOGIN / CADASTRO
# =============================
if not st.session_state.logado:

    st.title("🔐 Motor Financeiro SaaS")

    aba = st.radio("Acesso", ["Login", "Criar Conta"])

    # -------- CRIAR CONTA --------
    if aba == "Criar Conta":

        nome = st.text_input("Nome")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")

        if st.button("Cadastrar"):
            if criar_usuario(nome, email, senha):
                st.success("Conta criada! Aguarde liberação do administrador.")
            else:
                st.error("Email já cadastrado.")

    # -------- LOGIN --------
    else:
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            usuario = autenticar(email, senha)
            if usuario:
                if usuario[4] in ["aprovado", "admin"]:
                    st.session_state.logado = True
                    st.session_state.usuario = usuario
                    st.rerun()
                else:
                    st.warning("⏳ Seu acesso ainda não foi liberado.")
            else:
                st.error("Email ou senha inválidos.")

# =============================
# SISTEMA LOGADO
# =============================
else:

    usuario = st.session_state.usuario
    usuario_id = usuario[0]
    plano = usuario[4]

    st.sidebar.write(f"👤 {usuario[1]}")
    st.sidebar.write(f"Plano: {plano}")

    menu = ["Nova Empresa", "Histórico"]

    if plano == "admin":
        menu.append("Painel Admin")

    escolha = st.sidebar.selectbox("Menu", menu)

    # =============================
    # NOVA EMPRESA
    # =============================
    if escolha == "Nova
