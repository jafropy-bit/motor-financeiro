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

if "pagina" not in st.session_state:
    st.session_state.pagina = "login"

# =============================
# LOGIN / CADASTRO
# =============================
if not st.session_state.logado:

    aba = st.radio("Acesso", ["Login", "Criar Conta"])

    if aba == "Criar Conta":
        st.title("Criar Conta")

        nome = st.text_input("Nome")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")

        if st.button("Cadastrar"):
            if criar_usuario(nome, email, senha):
                st.success("Conta criada! Aguarde liberação.")
            else:
                st.error("Email já existe.")

    else:
        st.title("Login")

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
                    st.warning("Aguardando liberação do administrador.")
            else:
                st.error("Credenciais inválidas.")

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
    if escolha == "Nova Empresa":

        st.title("Cadastrar Empresa")

        nome_empresa = st.text_input("Nome da empresa")
        cnpj = st.text_input("CNPJ")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")

        if st.button("Salvar Empresa"):
            cursor.execute("""
            INSERT INTO empresas (usuario_id, nome_empresa, cnpj, cidade, estado, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (usuario_id, nome_empresa, cnpj, cidade, estado, datetime.now()))
            conn.commit()
            st.success("Empresa cadastrada.")

        st.divider()
        st.subheader("Inserir DRE")

        receita = st.number_input("Receita")
        custos = st.number_input("Custos")
        despesas = st.number_input("Despesas")
        impostos = st.number_input("Impostos")

        if st.button("Salvar DRE"):
            cursor.execute("SELECT id FROM empresas WHERE usuario_id=? ORDER BY id DESC LIMIT 1", (usuario_id,))
            empresa = cursor.fetchone()

            if empresa:
                cursor.execute("""
                INSERT INTO dre (empresa_id, receita, custos, despesas, impostos, data)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (empresa[0], receita, custos, despesas, impostos, datetime.now()))
                conn.commit()
                st.success("DRE salva.")

    # =============================
    # HISTÓRICO
    # =============================
    elif escolha == "Histórico":

        st.title("Histórico Financeiro")

        cursor.execute("""
        SELECT dre.receita, dre.custos, dre.despesas, dre.impostos, dre.data
        FROM dre
        JOIN empresas ON dre.empresa_id = empresas.id
        WHERE empresas.usuario_id=?
        """, (usuario_id,))

        dados = cursor.fetchall()

        if dados:
            df = pd.DataFrame(dados, columns=["Receita", "Custos", "Despesas", "Impostos", "Data"])
            st.dataframe(df)

            df["Lucro"] = df["Receita"] - df["Custos"] - df["Despesas"] - df["Impostos"]

            fig = px.line(df, x="Data", y="Lucro")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados ainda.")

    # =============================
    # PAINEL ADMIN
    # =============================
    elif escolha == "Painel Admin":

        st.title("Painel Administrativo")

        cursor.execute("SELECT id, nome, email, plano FROM usuarios")
        usuarios = cursor.fetchall()

        df = pd.DataFrame(usuarios, columns=["ID", "Nome", "Email", "Plano"])
        st.dataframe(df)

        user_id = st.number_input("ID do usuário para aprovar", step=1)

        if st.button("Aprovar Usuário"):
            cursor.execute("UPDATE usuarios SET plano='aprovado' WHERE id=?", (user_id,))
            conn.commit()
            st.success("Usuário aprovado.")

    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
