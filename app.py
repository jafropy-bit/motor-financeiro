import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import plotly.express as px

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# =========================
# CONEXÃO BANCO
# =========================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# =========================
# CRIAÇÃO TABELAS
# =========================

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
    email TEXT,
    telefone TEXT,
    whatsapp TEXT,
    cidade TEXT,
    estado TEXT,
    receita_bruta REAL,
    deducoes REAL,
    custos REAL,
    despesas REAL,
    depreciacao REAL,
    resultado_financeiro REAL,
    impostos REAL
)
""")

conn.commit()

# =========================
# CRIA ADMIN AUTOMÁTICO
# =========================

senha_admin = hashlib.sha256("admin123".encode()).hexdigest()

cursor.execute("SELECT * FROM usuarios WHERE email = ?", ("admin@motorfinanceiro.com",))
admin_existe = cursor.fetchone()

if not admin_existe:
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, plano) VALUES (?, ?, ?, ?)",
        ("Administrador", "admin@motorfinanceiro.com", senha_admin, "admin")
    )
    conn.commit()

# =========================
# FUNÇÕES
# =========================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def login(email, senha):
    senha_hash = hash_senha(senha)
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha_hash)
    )
    return cursor.fetchone()

# =========================
# NAVEGAÇÃO
# =========================

if "pagina" not in st.session_state:
    st.session_state.pagina = 1

# =========================
# PÁGINA 1 – DADOS EMPRESA
# =========================

if st.session_state.pagina == 1:

    st.title("Cadastro da Empresa")

    nome_empresa = st.text_input("Nome da empresa")
    cnpj = st.text_input("CNPJ")
    email_empresa = st.text_input("Email")
    telefone = st.text_input("Telefone")
    whatsapp = st.text_input("Whatsapp")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")

    if st.button("Próxima Página"):
        st.session_state.dados_empresa = {
            "nome_empresa": nome_empresa,
            "cnpj": cnpj,
            "email": email_empresa,
            "telefone": telefone,
            "whatsapp": whatsapp,
            "cidade": cidade,
            "estado": estado
        }
        st.session_state.pagina = 2
        st.rerun()

# =========================
# PÁGINA 2 – DADOS FINANCEIROS
# =========================

elif st.session_state.pagina == 2:

    st.title("Informações Financeiras")

    receita_bruta = st.number_input("Receita Operacional Bruta", value=0.0)
    deducoes = st.number_input("Deduções", value=0.0)
    custos = st.number_input("Custos (CMV/CPV)", value=0.0)
    despesas = st.number_input("Despesas Operacionais", value=0.0)
    depreciacao = st.number_input("Depreciação e Amortização", value=0.0)
    resultado_financeiro = st.number_input("Resultado Financeiro", value=0.0)
    impostos = st.number_input("IRPJ / CSLL", value=0.0)

    if st.button("Ir para Login"):
        st.session_state.dados_financeiros = {
            "receita_bruta": receita_bruta,
            "deducoes": deducoes,
            "custos": custos,
            "despesas": despesas,
            "depreciacao": depreciacao,
            "resultado_financeiro": resultado_financeiro,
            "impostos": impostos
        }
        st.session_state.pagina = 3
        st.rerun()

# =========================
# PÁGINA 3 – LOGIN
# =========================

elif st.session_state.pagina == 3:

    st.title("Login")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuario = login(email, senha)

        if usuario:
            st.session_state.usuario = usuario
            st.session_state.pagina = 4
            st.rerun()
        else:
            st.error("Login inválido")

# =========================
# PÁGINA 4 – RESULTADO DRE
# =========================

elif st.session_state.pagina == 4:

    st.title("Resultado DRE")

    dados = st.session_state.dados_financeiros

    receita_liquida = dados["receita_bruta"] - dados["deducoes"]
    lucro_bruto = receita_liquida - dados["custos"]
    ebitda = lucro_bruto - dados["despesas"]
    ebit = ebitda - dados["depreciacao"]
    lair = ebit + dados["resultado_financeiro"]
    lucro_liquido = lair - dados["impostos"]

    margem_ebitda = (ebitda / receita_liquida * 100) if receita_liquida != 0 else 0
    margem_bruta = (lucro_bruto / receita_liquida * 100) if receita_liquida != 0 else 0
    margem_liquida = (lucro_liquido / receita_liquida * 100) if receita_liquida != 0 else 0

    df = pd.DataFrame({
        "Indicador": ["Margem EBITDA", "Margem Bruta", "Margem Líquida"],
        "Valor (%)": [margem_ebitda, margem_bruta, margem_liquida]
    })

    st.subheader("Margens")
    st.dataframe(df)

    fig = px.bar(df, x="Indicador", y="Valor (%)")
    st.plotly_chart(fig, use_container_width=True)

    st.success("Análise concluída com sucesso!")
