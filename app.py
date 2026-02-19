import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# ---------------------------
# CONFIGURAÇÃO
# ---------------------------
VERSAO = "FREE"  # ALTERE PARA PREMIUM PARA LIBERAR

# ---------------------------
# SESSION STATE
# ---------------------------
if "logado" not in st.session_state:
    st.session_state.logado = False

if "empresa" not in st.session_state:
    st.session_state.empresa = {}

# ---------------------------
# LOGIN
# ---------------------------
if not st.session_state.logado:

    st.title("🔐 Login - Motor Financeiro")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        if email and senha:
            st.session_state.logado = True
            st.success("Login realizado com sucesso!")
            st.rerun()
        else:
            st.error("Preencha email e senha.")

    st.stop()

# ---------------------------
# CADASTRO EMPRESA
# ---------------------------
st.sidebar.title("🏢 Dados da Empresa")

empresa_nome = st.sidebar.text_input("Nome da Empresa")
cnpj = st.sidebar.text_input("CNPJ")
setor = st.sidebar.selectbox(
    "Setor",
    ["Comércio", "Serviços", "Indústria", "Tecnologia"]
)

st.session_state.empresa = {
    "nome": empresa_nome,
    "cnpj": cnpj,
    "setor": setor
}

# ---------------------------
# TÍTULO
# ---------------------------
st.title("📊 Motor Financeiro - Análise de DRE")

st.markdown(f"""
**Empresa:** {empresa_nome if empresa_nome else "Não informada"}  
**Setor:** {setor}
""")

st.divider()

# ---------------------------
# INPUT DRE
# ---------------------------
col1, col2 = st.columns(2)

with col1:
    receita = st.number_input("Receita Bruta", min_value=0.0)
    impostos = st.number_input("Impostos", min_value=0.0)
    custos = st.number_input("Custos", min_value=0.0)

with col2:
    despesas = st.number_input("Despesas Operacionais", min_value=0.0)
    depreciacao = st.number_input("Depreciação", min_value=0.0)
    juros = st.number_input("Juros", min_value=0.0)

# ---------------------------
# CÁLCULOS
# ---------------------------
if receita > 0:

    ebitda = receita - impostos - custos - despesas
    lucro_liquido = ebitda - depreciacao - juros

    margem_ebitda = (ebitda / receita) * 100
    margem_liquida = (lucro_liquido / receita) * 100

    score = 0

    if margem_ebitda > 20:
        score += 40
    elif margem_ebitda > 10:
        score += 25
    else:
        score += 10

    if margem_liquida > 10:
        score += 60
    elif margem_liquida > 5:
        score += 40
    else:
        score += 20

    st.divider()
    st.subheader("📈 Resultado da Análise")

    # ---------------- FREE ----------------
    if VERSAO == "FREE":

        st.metric("Margem EBITDA", f"{margem_ebitda:.2f}%")

        st.warning("🔒 Sua margem está abaixo da média do mercado.")
        st.info("Libere o Premium para visualizar Score completo, gráficos e relatório PDF.")

    # ---------------- PREMIUM ----------------
    if VERSAO == "PREMIUM":

        col3, col4, col5 = st.columns(3)

        col3.metric("Margem EBITDA", f"{margem_ebitda:.2f}%")
        col4.metric("Margem Líquida", f"{margem_liquida:.2f}%")
        col5.metric("Score Financeiro", f"{score}/100")

        df = pd.DataFrame({
            "Indicador": ["Receita", "EBITDA", "Lucro Líquido"],
            "Valor": [receita, ebitda]()
