import streamlit as st
import sqlite3
import bcrypt
import secrets
import string
from datetime import datetime

st.set_page_config(page_title="Plataforma Financeira", layout="wide")

# ========================
# CONEXÃO BANCO
# ========================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# ========================
# CRIAÇÃO DAS TABELAS
# ========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cnpj TEXT,
    pais_origem TEXT,
    pais_atuacao TEXT,
    email TEXT,
    telefone TEXT,
    whatsapp TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    email TEXT,
    senha BLOB,
    tipo TEXT
)
""")

conn.commit()

# ========================
# MIGRAÇÃO AUTOMÁTICA (caso tabela antiga exista)
# ========================

try:
    cursor.execute("ALTER TABLE empresas ADD COLUMN status TEXT")
    conn.commit()
except:
    pass

# ========================
# FUNÇÕES
# ========================

def gerar_hash(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt())

def verificar_senha(senha_digitada, senha_hash):
    return bcrypt.checkpw(senha_digitada.encode(), senha_hash)

def gerar_senha_automatica():
    caracteres = string.ascii_letters + string.digits + "!@#"
    return ''.join(secrets.choice(caracteres) for _ in range(10))

# ========================
# SESSION STATE
# ========================

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.tipo = None

# ========================
# FORMULÁRIO PÚBLICO
# ========================

def formulario_publico():
    st.title("Cadastro da Empresa")

    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    pais_origem = st.text_input("País de Origem")

    pais_atuacao = st.selectbox(
        "País de Atuação",
        ["Brasil", "Estados Unidos", "Portugal", "Canadá"]
    )

    email = st.text_input("E-mail")
    telefone = st.text_input("Telefone Fixo (+País +DDD +Número)")
    whatsapp = st.text_input("WhatsApp (+País +DDD +Número)")

    if st.button("Enviar Cadastro"):

        cursor.execute("""
        INSERT INTO empresas
        (nome, cnpj, pais_origem, pais_atuacao, email, telefone, whatsapp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, cnpj, pais_origem, pais_atuacao, email, telefone, whatsapp, "pendente"))

        conn.commit()

        st.success("Cadastro enviado com sucesso! Aguarde liberação de acesso.")

# ========================
# LOGIN CLIENTE
# ========================

def tela_login():
    st.title("Login Cliente")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):

        cursor.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        usuario = cursor.fetchone()

        if usuario and verificar_senha(senha, usuario[3]):
            st.session_state.logado = True
            st.session_state.empresa_id = usuario[1]
            st.session_state.tipo = usuario[4]
            st.rerun()
        else:
            st.error("Credenciais inválidas")

# ========================
# PAINEL SUPER ADMIN
# ========================

def painel_admin():
    st.title("Painel Super Admin")

    cursor.execute("SELECT * FROM empresas WHERE status='pendente'")
    pendentes = cursor.fetchall()

    if not pendentes:
        st.info("Nenhuma empresa pendente.")
        return

    for empresa in pendentes:
        st.write("---")
        st.write(f"ID: {empresa[0]}")
        st.write(f"Empresa: {empresa[1]}")
        st.write(f"E-mail: {empresa[5]}")
        st.write(f"Telefone: {empresa[6]}")
        st.write(f"WhatsApp: {empresa[7]}")
