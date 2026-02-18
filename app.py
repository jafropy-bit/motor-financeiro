import streamlit as st
import sqlite3
import hashlib
import secrets
import string
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import Table
from reportlab.lib.styles import getSampleStyleSheet
import os

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# =========================
# BANCO
# =========================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

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

# =========================
# FUNÇÕES
# =========================

def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def gerar_senha():
    return ''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(10))

def calcular_score(margem_liquida):
    if margem_liquida >= 20:
        return 90
    elif margem_liquida >= 10:
        return 70
    elif margem_liquida >= 5:
        return 50
    else:
        return 30

def gerar_pdf(nome, dados):
    file_name = f"relatorio_{nome}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"Relatório Financeiro - {nome}", styles['Heading1']))
    elements.append(Spacer(1, 0.5 * inch))

    for chave, valor in dados.items():
        elements.append(Paragraph(f"{chave}: {valor}", styles['Normal']))
        elements.append(Spacer(1, 0.2 * inch))

    doc.build(elements)
    return file_name

# =========================
# SESSION
# =========================

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.plano = None

# =========================
# CADASTRO FREE
# =========================

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
        lucro_liquido = receita - impostos - custos - despesas
        margem_ebitda = (ebitda / receita) * 100 if receita > 0 else 0
        margem_liquida = (lucro_liquido / receita) * 100 if receita > 0 else 0
        score = calcular_score(margem_liquida)

        cursor.execute("""
        INSERT INTO empresas (nome, cnpj, email, telefone, status, plano)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (nome, cnpj, email, telefone, "pendente", "free"))

        empresa_id = cursor.lastrowid

        cursor.execute("""
        INSERT INTO dre
        (empresa_id, receita, impostos, custos, despesas,
        ebitda, lucro_liquido, margem_ebitda, margem_liquida, score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (empresa_id, receita, impostos, custos, despesas,
              ebitda, lucro_liquido, margem_ebitda, margem_liquida, score))

        conn.commit()

        st.success("Diagnóstico Gerado!")

        # ===== TEASER =====
        st.subheader("Resumo Gratuito")

        if margem_liquida < 10:
            st.warning("Sua margem está abaixo da média do mercado.")
        else:
            st.success("Sua margem está saudável.")

        st.info("Libere o acesso Premium para ver gráficos detalhados e baixar o relatório completo.")

# =========================
# LOGIN
# =========================

def login():
    st.title("Login Cliente")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        user = cursor.fetchone()

        if user and gerar_hash(senha) == user[3]:
            st.session_state.logado = True
            st.session_state.empresa_id = user[1]

            cursor.execute("SELECT plano FROM empresas WHERE id=?", (user[1],))
            plano = cursor.fetchone()[0]
            st.session_state.plano = plano

            st.rerun()
        else:
            st.error("Credenciais inválidas")

# =========================
# DASHBOARD
# =========================

def dashboard():
    st.title("Painel Financeiro")

    cursor.execute("SELECT nome, plano FROM empresas WHERE id=?", (st.session_state.empresa_id,))
    empresa = cursor.fetchone()

    cursor.execute("SELECT * FROM dre WHERE empresa_id=?", (st.session_state.empresa_id,))
    dre = cursor.fetchone()

    receita = dre[2]
    lucro = dre[7]
    margem_liquida = dre[9]
    score = dre[10]

    st.metric("Margem Líquida (%)", round(margem_liquida,2))
    st.metric("Score Financeiro", score)

    if st.session_state.plano == "premium":

        fig = plt.figure()
        plt.bar(["Receita", "Lucro"], [receita, lucro])
        st.pyplot(fig)

        dados = {
            "Receita": receita,
            "Lucro Líquido": lucro,
            "Margem Líquida (%)": margem_liquida,
            "Score": score
        }

        pdf = gerar_pdf(empresa[0], dados)

        with open(pdf, "rb") as f:
            st.download_button("Baixar Relatório PDF", f, file_name=pdf)

    else:
        st.warning("Plano Free não inclui gráficos nem PDF.")

# =========================
# SUPER ADMIN
# =========================

def super_admin():
    st.title("Painel Super Admin")

    cursor.execute("SELECT * FROM empresas WHERE status='pendente'")
    empresas = cursor.fetchall()

    for emp in empresas:
        st.write("---")
        st.write(emp[1], "-", emp[2])

        if st.button(f"Liberar Premium {emp[0]}"):

            senha = gerar_senha()
            senha_hash = gerar_hash(senha)

            cursor.execute("""
            INSERT INTO usuarios (empresa_id, email, senha)
            VALUES (?, ?, ?)
            """, (emp[0], emp[3], senha_hash))

            cursor.execute("""
            UPDATE empresas SET status='ativo', plano='premium'
            WHERE id=?
            """, (emp[0],))

            conn.commit()

            st.success(f"Acesso liberado! Senha: {senha}")

# =========================
# MENU
# =========================

menu = st.sidebar.selectbox("Menu", ["Diagnóstico Gratuito", "Login", "Super Admin"])

if not st.session_state.logado:

    if menu == "Diagnóstico Gratuito":
        cadastro_free()
    elif menu == "Login":
        login()
    elif menu == "Super Admin":
        super_admin()

else:
    dashboard()
