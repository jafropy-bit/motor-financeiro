import streamlit as st
import sqlite3
import bcrypt
from datetime import datetime

st.set_page_config(page_title="SaaS Financeiro", layout="wide")

# =========================
# CONEXÃO COM BANCO
# =========================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# CRIAÇÃO DAS TABELAS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cnpj TEXT,
    pais_origem TEXT,
    pais_atuacao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    nome TEXT,
    email TEXT UNIQUE,
    senha BLOB,
    tipo TEXT,
    aceitou_politica INTEGER,
    data_aceite TEXT,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dados_financeiros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    receita REAL,
    impostos REAL,
    despesas REAL,
    data_lancamento TEXT,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id)
)
""")

conn.commit()

# =========================
# SESSION STATE
# =========================

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_id = None
    st.session_state.empresa_id = None
    st.session_state.tipo = None

# =========================
# FUNÇÃO HASH SENHA
# =========================

def gerar_hash(senha):
    return bcrypt.hashpw(senha.encode(), bcrypt.gensalt())

def verificar_senha(senha_digitada, senha_hash):
    return bcrypt.checkpw(senha_digitada.encode(), senha_hash)

# =========================
# TELA LOGIN
# =========================

def tela_login():
    st.title("Login")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        usuario = cursor.fetchone()

        if usuario and verificar_senha(senha, usuario[4]):
            st.session_state.logado = True
            st.session_state.usuario_id = usuario[0]
            st.session_state.empresa_id = usuario[1]
            st.session_state.tipo = usuario[5]
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Credenciais inválidas")

# =========================
# CADASTRO EMPRESA
# =========================

def tela_cadastro():
    st.title("Cadastro de Empresa")

    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    pais_origem = st.text_input("País de Origem")

    pais_atuacao = st.selectbox(
        "País de Atuação",
        ["Brasil", "Estados Unidos", "Portugal", "Canadá"]
    )

    st.markdown("### Criar Usuário Administrador")

    nome_user = st.text_input("Nome do Admin")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    aceite = st.checkbox("Li e concordo com a Política de Privacidade")

    if st.button("Cadastrar"):
        if not aceite:
            st.error("Você precisa aceitar a Política de Privacidade.")
            return

        senha_hash = gerar_hash(senha)

        cursor.execute("""
        INSERT INTO empresas (nome, cnpj, pais_origem, pais_atuacao)
        VALUES (?, ?, ?, ?)
        """, (nome, cnpj, pais_origem, pais_atuacao))

        empresa_id = cursor.lastrowid

        cursor.execute("""
        INSERT INTO usuarios 
        (empresa_id, nome, email, senha, tipo, aceitou_politica, data_aceite)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            empresa_id,
            nome_user,
            email,
            senha_hash,
            "admin",
            1,
            datetime.now().isoformat()
        ))

        conn.commit()
        st.success("Empresa cadastrada com sucesso!")

# =========================
# DASHBOARD
# =========================

def dashboard():
    st.title("Dashboard Financeiro")

    if st.session_state.tipo not in ["admin", "usuario"]:
        st.error("Acesso negado.")
        st.stop()

    st.subheader("Inserir Dados Financeiros")

    receita = st.number_input("Receita")
    impostos = st.number_input("Impostos")
    despesas = st.number_input("Despesas")

    if st.button("Salvar Dados"):
        cursor.execute("""
        INSERT INTO dados_financeiros
        (empresa_id, receita, impostos, despesas, data_lancamento)
        VALUES (?, ?, ?, ?, ?)
        """, (
            st.session_state.empresa_id,
            receita,
            impostos,
            despesas,
            datetime.now().isoformat()
        ))
        conn.commit()
        st.success("Dados salvos!")

    st.subheader("DRE")

    cursor.execute("""
    SELECT receita, impostos, despesas 
    FROM dados_financeiros 
    WHERE empresa_id = ?
    """, (st.session_state.empresa_id,))

    dados = cursor.fetchall()

    total_receita = sum([d[0] for d in dados])
    total_impostos = sum([d[1] for d in dados])
    total_despesas = sum([d[2] for d in dados])
    lucro = total_receita - total_impostos - total_despesas

    st.write("Receita Total:", total_receita)
    st.write("Impostos:", total_impostos)
    st.write("Despesas:", total_despesas)
    st.write("Lucro Líquido:", lucro)

    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()

# =========================
# MENU PRINCIPAL
# =========================

menu = st.sidebar.selectbox("Menu", ["Login", "Cadastrar Empresa"])

if not st.session_state.logado:
    if menu == "Login":
        tela_login()
    else:
        tela_cadastro()
else:
    dashboard()
