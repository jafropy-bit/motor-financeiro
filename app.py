import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import plotly.express as px
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io
from datetime import datetime

# ==========================
# CONFIG
# ==========================

st.set_page_config(page_title="Motor Financeiro SaaS", layout="wide")

# ==========================
# BANCO DE DADOS
# ==========================

conn = sqlite3.connect("motor_financeiro.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT UNIQUE,
    senha TEXT,
    plano TEXT DEFAULT 'free',
    aprovado INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    nome_empresa TEXT,
    cnpj TEXT,
    receita REAL,
    lucro REAL,
    data TEXT
)
""")

conn.commit()

# ==========================
# CRIAR ADMIN AUTOMÁTICO
# ==========================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

admin_email = "admin@motorfinanceiro.com"
admin_senha = hash_senha("123456")

cursor.execute("SELECT * FROM usuarios WHERE email=?", (admin_email,))
if not cursor.fetchone():
    cursor.execute(
        "INSERT INTO usuarios (nome,email,senha,plano,aprovado) VALUES (?,?,?,?,?)",
        ("Administrador", admin_email, admin_senha, "admin", 1)
    )
    conn.commit()

# ==========================
# FUNÇÃO PDF
# ==========================

def gerar_pdf(nome_empresa, dados):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.drawString(50, 800, f"Relatório Financeiro - {nome_empresa}")
    y = 760
    for linha in dados:
        c.drawString(50, y, linha)
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer

# ==========================
# SESSION
# ==========================

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ==========================
# LOGIN ADMIN (CANTO SUPERIOR)
# ==========================

with st.sidebar:
    st.subheader("🔐 Login Admin")
    admin_login = st.text_input("Email Admin")
    admin_pass = st.text_input("Senha Admin", type="password")
    if st.button("Entrar Admin"):
        cursor.execute("SELECT * FROM usuarios WHERE email=? AND senha=?",
                       (admin_login, hash_senha(admin_pass)))
        user = cursor.fetchone()
        if user and user[4] == "admin":
            st.session_state.usuario = user
        else:
            st.error("Acesso negado")

# ==========================
# PAINEL ADMIN
# ==========================

if st.session_state.usuario and st.session_state.usuario[4] == "admin":

    st.title("👑 Painel Admin")

    cursor.execute("SELECT id,nome,email,plano,aprovado FROM usuarios WHERE plano!='admin'")
    usuarios = cursor.fetchall()

    for u in usuarios:
        st.write(f"**{u[1]}** | {u[2]} | Plano: {u[3]} | Aprovado: {u[4]}")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(f"Aprovar {u[0]}"):
                cursor.execute("UPDATE usuarios SET aprovado=1 WHERE id=?", (u[0],))
                conn.commit()
                st.rerun()

        with col2:
            if st.button(f"Tornar Premium {u[0]}"):
                cursor.execute("UPDATE usuarios SET plano='premium' WHERE id=?", (u[0],))
                conn.commit()
                st.rerun()

    st.stop()

# ==========================
# PÁGINA 1 - CADASTRO
# ==========================

st.title("🚀 Cadastro da Empresa")

nome = st.text_input("Nome")
email = st.text_input("Email")
senha = st.text_input("Senha", type="password")

if st.button("Cadastrar"):
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome,email,senha) VALUES (?,?,?)",
            (nome, email, hash_senha(senha))
        )
        conn.commit()
        st.success("Cadastro realizado! Aguarde aprovação do admin.")
    except:
        st.error("Email já cadastrado.")

st.divider()

# ==========================
# PÁGINA 2 - LOGIN USUÁRIO
# ==========================

st.subheader("🔐 Login Usuário")

login_email = st.text_input("Email Login")
login_senha = st.text_input("Senha Login", type="password")

if st.button("Entrar"):
    cursor.execute("SELECT * FROM usuarios WHERE email=? AND senha=?",
                   (login_email, hash_senha(login_senha)))
    user = cursor.fetchone()
    if user:
        if user[5] == 0:
            st.warning("Aguardando aprovação do administrador.")
        else:
            st.session_state.usuario = user
            st.rerun()
    else:
        st.error("Login inválido")

# ==========================
# PÁGINA 3 - RESULTADOS
# ==========================

if st.session_state.usuario and st.session_state.usuario[4] != "admin":

    usuario = st.session_state.usuario

    st.title("📊 Simulador Financeiro")

    receita = st.number_input("Receita Bruta")
    custos = st.number_input("Custos")
    despesas = st.number_input("Despesas")

    if st.button("Calcular"):

        lucro_bruto = receita - custos
        lucro_liquido = lucro_bruto - despesas

        margem = 0
        if receita > 0:
            margem = (lucro_liquido / receita) * 100

        cursor.execute(
            "INSERT INTO empresas (usuario_id,nome_empresa,receita,lucro,data) VALUES (?,?,?,?,?)",
            (usuario[0], usuario[1], receita, lucro_liquido, str(datetime.now()))
        )
        conn.commit()

        if usuario[4] == "free":
            st.warning("Plano FREE — Faça upgrade para ver dashboard completo.")
            st.write(f"Lucro Líquido: R$ {lucro_liquido}")
            st.stop()

        # DASHBOARD PREMIUM
        st.subheader("📈 Dashboard Premium")

        df = pd.DataFrame({
            "Indicador": ["Receita", "Lucro Líquido"],
            "Valor": [receita, lucro_liquido]
        })

        fig = px.bar(df, x="Indicador", y="Valor")
        st.plotly_chart(fig, use_container_width=True)

        st.metric("Margem Líquida (%)", round(margem, 2))

        relatorio = [
            f"Receita: {receita}",
            f"Lucro Líquido: {lucro_liquido}",
            f"Margem: {round(margem,2)}%"
        ]

        pdf = gerar_pdf(usuario[1], relatorio)

        st.download_button(
            "📄 Baixar PDF",
            pdf,
            file_name="relatorio_financeiro.pdf"
        )

    st.divider()

    st.subheader("📜 Histórico")

    cursor.execute("SELECT nome_empresa,receita,lucro,data FROM empresas WHERE usuario_id=?",
                   (usuario[0],))
    historico = cursor.fetchall()

    for h in historico:
        st.write(f"{h[3]} | Receita: {h[1]} | Lucro: {h[2]}")
