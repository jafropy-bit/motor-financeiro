import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import sqlite3
import hashlib

st.set_page_config(page_title="Motor Financeiro SaaS", layout="wide")

# ------------------------
# DATABASE
# ------------------------
conn = sqlite3.connect("usuarios.db", check_same_thread=False)
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
conn.commit()

# ------------------------
# FUNÇÕES
# ------------------------
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(nome, email, senha):
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, plano) VALUES (?, ?, ?, ?)",
            (nome, email, hash_senha(senha), "free")
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

# ------------------------
# SESSION
# ------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "pagina" not in st.session_state:
    st.session_state.pagina = "login"

# =========================
# CADASTRO
# =========================
if st.session_state.pagina == "cadastro":

    st.title("📝 Criar Conta")

    nome = st.text_input("Nome")
    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Cadastrar"):
        if criar_usuario(nome, email, senha):
            st.success("Conta criada com sucesso!")
            st.session_state.pagina = "login"
            st.rerun()
        else:
            st.error("Email já cadastrado.")

    if st.button("Voltar para Login"):
        st.session_state.pagina = "login"
        st.rerun()

# =========================
# LOGIN
# =========================
elif st.session_state.pagina == "login":

    st.title("🔐 Login")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuario = autenticar(email, senha)
        if usuario:
            st.session_state.logado = True
            st.session_state.usuario = usuario
            st.session_state.pagina = "empresa"
            st.rerun()
        else:
            st.error("Email ou senha inválidos.")

    if st.button("Criar Conta"):
        st.session_state.pagina = "cadastro"
        st.rerun()

# =========================
# PÁGINA EMPRESA
# =========================
elif st.session_state.pagina == "empresa" and st.session_state.logado:

    st.title("🏢 Dados da Empresa")

    nome_empresa = st.text_input("Nome da empresa")
    cnpj = st.text_input("CNPJ")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")

    if st.button("Próxima"):
        st.session_state.pagina = "dre"
        st.session_state.empresa = nome_empresa
        st.rerun()

# =========================
# PÁGINA DRE
# =========================
elif st.session_state.pagina == "dre":

    st.title("📊 Inserir Dados da DRE")

    receita = st.number_input("Receita Bruta", min_value=0.0)
    custos = st.number_input("Custos", min_value=0.0)
    despesas = st.number_input("Despesas", min_value=0.0)

    if st.button("Ver Resultado"):
        st.session_state.receita = receita
        st.session_state.custos = custos
        st.session_state.despesas = despesas
        st.session_state.pagina = "resultado"
        st.rerun()

# =========================
# RESULTADO
# =========================
elif st.session_state.pagina == "resultado":

    st.title("📈 Resultado Financeiro")

    receita = st.session_state.receita
    custos = st.session_state.custos
    despesas = st.session_state.despesas

    lucro = receita - custos - despesas
    margem = (lucro / receita) * 100 if receita > 0 else 0

    st.metric("Lucro", f"R$ {lucro:,.2f}")
    st.metric("Margem (%)", f"{margem:.2f}%")

    df = pd.DataFrame({
        "Indicador": ["Receita", "Custos", "Despesas", "Lucro"],
        "Valor": [receita, custos, despesas, lucro]
    })

    fig = px.bar(df, x="Indicador", y="Valor")
    st.plotly_chart(fig, use_container_width=True)

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
