import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import TableStyle
from reportlab.lib.pagesizes import A4
from datetime import datetime

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# ==============================
# CONEXÃO
# ==============================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# ==============================
# RECRIA TABELA USUÁRIOS CORRETAMENTE
# ==============================

cursor.execute("DROP TABLE IF EXISTS usuarios")
cursor.execute("""
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT UNIQUE,
    senha TEXT,
    plano TEXT
)
""")

# ==============================
# RECRIA TABELA EMPRESAS
# ==============================

cursor.execute("DROP TABLE IF EXISTS empresas")
cursor.execute("""
CREATE TABLE empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    nome_empresa TEXT,
    cnpj TEXT,
    cidade TEXT,
    estado TEXT,
    receita REAL,
    lucro REAL,
    data TEXT
)
""")

conn.commit()

# ==============================
# CRIA ADMIN GARANTIDO
# ==============================

senha_admin = hashlib.sha256("admin123".encode()).hexdigest()

cursor.execute("""
INSERT INTO usuarios (nome, email, senha, plano)
VALUES (?, ?, ?, ?)
""", ("Administrador", "admin@motorfinanceiro.com", senha_admin, "admin"))

conn.commit()

# ==============================
# FUNÇÕES
# ==============================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def login(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
        (email, hash_senha(senha))
    )
    return cursor.fetchone()

def gerar_pdf(nome_empresa, df):
    nome_arquivo = f"relatorio_{nome_empresa}.pdf"
    doc = SimpleDocTemplate(nome_arquivo, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Relatório DRE - {nome_empresa}", styles["Title"]))
    elements.append(Spacer(1, 20))

    data = [df.columns.tolist()] + df.values.tolist()
    tabela = Table(data)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    elements.append(tabela)
    doc.build(elements)
    return nome_arquivo

# ==============================
# CONTROLE DE PÁGINA
# ==============================

if "pagina" not in st.session_state:
    st.session_state.pagina = 1

# ==============================
# BOTÃO ADMIN
# ==============================

col1, col2 = st.columns([9,1])
with col2:
    if st.button("Admin"):
        st.session_state.pagina = "admin"

# ==============================
# PÁGINA 1
# ==============================

if st.session_state.pagina == 1:

    st.title("Cadastro da Empresa")

    nome = st.text_input("Nome da empresa")
    cnpj = st.text_input("CNPJ")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")

    if st.button("Próxima"):
        st.session_state.empresa = {
            "nome": nome,
            "cnpj": cnpj,
            "cidade": cidade,
            "estado": estado
        }
        st.session_state.pagina = 2
        st.rerun()

# ==============================
# PÁGINA 2
# ==============================

elif st.session_state.pagina == 2:

    st.title("Informações Financeiras")

    receita = st.number_input("Receita Bruta", value=0.0)
    custos = st.number_input("Custos", value=0.0)
    despesas = st.number_input("Despesas", value=0.0)
    impostos = st.number_input("Impostos", value=0.0)

    if st.button("Ir para Login"):
        st.session_state.financeiro = {
            "receita": receita,
            "custos": custos,
            "despesas": despesas,
            "impostos": impostos
        }
        st.session_state.pagina = 3
        st.rerun()

# ==============================
# PÁGINA 3 LOGIN
# ==============================

elif st.session_state.pagina == 3:

    st.title("Login para visualizar resultado")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuario = login(email, senha)
        if usuario:
            st.session_state.usuario = usuario
            st.session_state.pagina = 4
            st.rerun()
        else:
            st.error("Acesso negado")

# ==============================
# PÁGINA 4 RESULTADO
# ==============================

elif st.session_state.pagina == 4:

    dados = st.session_state.financeiro
    empresa = st.session_state.empresa
    usuario = st.session_state.usuario

    receita = dados["receita"]
    lucro = receita - dados["custos"] - dados["despesas"] - dados["impostos"]
    margem = (lucro / receita * 100) if receita else 0

    df = pd.DataFrame({
        "Indicador": ["Receita", "Lucro Líquido", "Margem (%)"],
        "Valor": [receita, lucro, margem]
    })

    st.dataframe(df)

    fig = px.bar(df, x="Indicador", y="Valor")
    st.plotly_chart(fig, use_container_width=True)

# ==============================
# PAINEL ADMIN
# ==============================

elif st.session_state.pagina == "admin":

    st.title("Painel Administrativo")

    email = st.text_input("Email Admin")
    senha = st.text_input("Senha Admin", type="password")

    if st.button("Entrar Admin"):
        usuario = login(email, senha)
        if usuario and usuario[4] == "admin":
            st.success("Bem-vindo Admin")
            st.dataframe(pd.read_sql_query("SELECT * FROM usuarios", conn))
        else:
            st.error("Acesso negado")
