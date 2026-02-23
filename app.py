import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Motor Financeiro SaaS", layout="wide")

# ===============================
# BANCO
# ===============================

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
    usuario_email TEXT,
    nome_empresa TEXT,
    cnpj TEXT,
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
    impostos REAL,
    data TEXT
)
""")

conn.commit()

# ===============================
# FUNÇÕES
# ===============================

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

# ===============================
# SESSION
# ===============================

if "etapa" not in st.session_state:
    st.session_state.etapa = 1

if "dados_empresa" not in st.session_state:
    st.session_state.dados_empresa = {}

if "dados_financeiros" not in st.session_state:
    st.session_state.dados_financeiros = {}

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ===============================
# PAGINA 1 - DADOS EMPRESA
# ===============================

if st.session_state.etapa == 1:

    st.title("📋 Cadastro da Empresa")

    nome_empresa = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    email = st.text_input("Email")
    telefone = st.text_input("Telefone")
    whatsapp = st.text_input("Whatsapp")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")

    if st.button("Próximo"):
        st.session_state.dados_empresa = {
            "nome_empresa": nome_empresa,
            "cnpj": cnpj,
            "email": email,
            "telefone": telefone,
            "whatsapp": whatsapp,
            "cidade": cidade,
            "estado": estado
        }
        st.session_state.etapa = 2
        st.rerun()

# ===============================
# PAGINA 2 - DRE
# ===============================

elif st.session_state.etapa == 2:

    st.title("📊 Informações Financeiras - DRE")

    receita_bruta = st.number_input("(+) Receita Operacional Bruta", min_value=0.0)
    deducoes = st.number_input("(-) Deduções (Impostos s/ vendas, devoluções)", min_value=0.0)

    custos = st.number_input("(-) Custos (CMV/CPV)", min_value=0.0)
    despesas = st.number_input("(-) Despesas Operacionais (SG&A)", min_value=0.0)
    depreciacao = st.number_input("(-) Depreciação e Amortização", min_value=0.0)
    resultado_financeiro = st.number_input("(+) / (-) Resultado Financeiro", value=0.0)
    impostos = st.number_input("(-) IRPJ / CSLL", min_value=0.0)

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
        st.session_state.etapa = 3
        st.rerun()

# ===============================
# PAGINA 3 - LOGIN
# ===============================

elif st.session_state.etapa == 3:

    st.title("🔐 Login para Visualizar Resultados")

    email_login = st.text_input("Email")
    senha_login = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE email=? AND senha=?",
                       (email_login, hash_senha(senha_login)))
        user = cursor.fetchone()

        if user:
            if user[5] == 0:
                st.warning("Usuário aguardando aprovação do administrador.")
            else:
                st.session_state.usuario = user
                st.session_state.etapa = 4
                st.rerun()
        else:
            st.error("Login inválido")

# ===============================
# PAGINA 4 - RESULTADOS
# ===============================

elif st.session_state.etapa == 4:

    st.title("📈 Resultado do DRE")

    empresa = st.session_state.dados_empresa
    financeiro = st.session_state.dados_financeiros

    # ===============================
    # CÁLCULOS DRE
    # ===============================

    receita_liquida = financeiro["receita_bruta"] - financeiro["deducoes"]
    lucro_bruto = receita_liquida - financeiro["custos"]
    ebitda = lucro_bruto - financeiro["despesas"]
    ebit = ebitda - financeiro["depreciacao"]
    lair = ebit + financeiro["resultado_financeiro"]
    lucro_liquido = lair - financeiro["impostos"]

    margem_ebitda = (ebitda / receita_liquida * 100) if receita_liquida else 0
    margem_bruta = (lucro_bruto / receita_liquida * 100) if receita_liquida else 0
    margem_liquida = (lucro_liquido / receita_liquida * 100) if receita_liquida else 0

    # ===============================
    # SALVAR NO BANCO
    # ===============================

    cursor.execute("""
    INSERT INTO empresas (
    usuario_email,nome_empresa,cnpj,telefone,whatsapp,cidade,estado,
    receita_bruta,deducoes,custos,despesas,depreciacao,
    resultado_financeiro,impostos,data)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,
    (
        empresa["email"],
        empresa["nome_empresa"],
        empresa["cnpj"],
        empresa["telefone"],
        empresa["whatsapp"],
        empresa["cidade"],
        empresa["estado"],
        financeiro["receita_bruta"],
        financeiro["deducoes"],
        financeiro["custos"],
        financeiro["despesas"],
        financeiro["depreciacao"],
        financeiro["resultado_financeiro"],
        financeiro["impostos"],
        str(datetime.now())
    ))

    conn.commit()

    # ===============================
    # EXIBIÇÃO
    # ===============================

    st.subheader("📊 Indicadores")

    col1, col2, col3 = st.columns(3)

    col1.metric("Margem EBITDA (%)", round(margem_ebitda, 2))
    col2.metric("Margem Bruta (%)", round(margem_bruta, 2))
    col3.metric("Margem Líquida (%)", round(margem_liquida, 2))

    df = pd.DataFrame({
        "Indicador": ["Receita Líquida", "Lucro Bruto", "EBITDA", "Lucro Líquido"],
        "Valor": [receita_liquida, lucro_bruto, ebitda, lucro_liquido]
    })

    fig = px.bar(df, x="Indicador", y="Valor")
    st.plotly_chart(fig, use_container_width=True)

    st.success("Relatório gerado com sucesso.")
