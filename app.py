import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# ---------------------------
# SESSION STATE
# ---------------------------
if "pagina" not in st.session_state:
    st.session_state.pagina = 1

if "logado" not in st.session_state:
    st.session_state.logado = False

if "empresa" not in st.session_state:
    st.session_state.empresa = {}

if "dre" not in st.session_state:
    st.session_state.dre = {}

# ===========================
# PÁGINA 1 - DADOS EMPRESA
# ===========================
if st.session_state.pagina == 1:

    st.title("🏢 Cadastro da Empresa")

    nome = st.text_input("Nome da empresa")
    cnpj = st.text_input("CNPJ")
    email = st.text_input("Email")
    telefone = st.text_input("Telefone")
    whatsapp = st.text_input("Whatsapp")
    cidade = st.text_input("Cidade")
    estado = st.text_input("Estado")

    if st.button("Próxima Página"):
        st.session_state.empresa = {
            "nome": nome,
            "cnpj": cnpj,
            "email": email,
            "telefone": telefone,
            "whatsapp": whatsapp,
            "cidade": cidade,
            "estado": estado,
        }
        st.session_state.pagina = 2
        st.rerun()

# ===========================
# PÁGINA 2 - DRE
# ===========================
elif st.session_state.pagina == 2:

    st.title("📊 Demonstração de Resultado do Exercício")

    receita_bruta = st.number_input("Receita Operacional Bruta", min_value=0.0)
    deducoes = st.number_input("Deduções (Impostos / Devoluções)", min_value=0.0)
    custos = st.number_input("Custos (CMV/CPV)", min_value=0.0)
    despesas = st.number_input("Despesas Operacionais (SG&A)", min_value=0.0)
    depreciacao = st.number_input("Depreciação e Amortização", min_value=0.0)
    resultado_financeiro = st.number_input("Resultado Financeiro", value=0.0)
    impostos = st.number_input("IRPJ / CSLL", min_value=0.0)

    if st.button("Continuar para Login"):
        st.session_state.dre = {
            "receita_bruta": receita_bruta,
            "deducoes": deducoes,
            "custos": custos,
            "despesas": despesas,
            "depreciacao": depreciacao,
            "resultado_financeiro": resultado_financeiro,
            "impostos": impostos,
        }
        st.session_state.pagina = 3
        st.rerun()

# ===========================
# PÁGINA 3 - LOGIN
# ===========================
elif st.session_state.pagina == 3:

    st.title("🔐 Acesso aos Resultados")

    EMAIL_CORRETO = "admin@motorfinanceiro.com"
SENHA_CORRETA = "123456"


    if st.button("Entrar"):
        if email and senha:
            st.session_state.logado = True
            st.session_state.pagina = 4
            st.rerun()
        else:
            st.error("Preencha email e senha.")

# ===========================
# PÁGINA 4 - RESULTADOS
# ===========================
elif st.session_state.pagina == 4 and st.session_state.logado:

    st.title("📈 Resultado da Análise DRE")

    dre = st.session_state.dre

    receita_liquida = dre["receita_bruta"] - dre["deducoes"]
    lucro_bruto = receita_liquida - dre["custos"]
    ebitda = lucro_bruto - dre["despesas"]
    ebit = ebitda - dre["depreciacao"]
    lair = ebit + dre["resultado_financeiro"]
    lucro_liquido = lair - dre["impostos"]

    margem_ebitda = (ebitda / receita_liquida) * 100 if receita_liquida > 0 else 0
    margem_bruta = (lucro_bruto / receita_liquida) * 100 if receita_liquida > 0 else 0
    margem_liquida = (lucro_liquido / receita_liquida) * 100 if receita_liquida > 0 else 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Margem EBITDA (%)", f"{margem_ebitda:.2f}%")
    col2.metric("Margem Bruta (%)", f"{margem_bruta:.2f}%")
    col3.metric("Margem Líquida (%)", f"{margem_liquida:.2f}%")

    # ---------------- GRÁFICO ----------------
    df = pd.DataFrame({
        "Indicador": ["Receita Líquida", "Lucro Bruto", "EBITDA", "Lucro Líquido"],
        "Valor": [receita_liquida, lucro_bruto, ebitda, lucro_liquido]
    })

    fig = px.bar(df, x="Indicador", y="Valor")
    st.plotly_chart(fig, use_container_width=True)

    # ---------------- PDF ----------------
    if st.button("📄 Gerar Relatório PDF"):

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=11)

        pdf.cell(200, 8, "Relatório Financeiro - DRE", ln=True)
        pdf.cell(200, 8, f"Empresa: {st.session_state.empresa['nome']}", ln=True)
        pdf.cell(200, 8, f"Receita Liquida: {receita_liquida:.2f}", ln=True)
        pdf.cell(200, 8, f"Lucro Bruto: {lucro_bruto:.2f}", ln=True)
        pdf.cell(200, 8, f"EBITDA: {ebitda:.2f}", ln=True)
        pdf.cell(200, 8, f"Lucro Liquido: {lucro_liquido:.2f}", ln=True)
        pdf.cell(200, 8, f"Margem EBITDA: {margem_ebitda:.2f}%", ln=True)
        pdf.cell(200, 8, f"Margem Bruta: {margem_bruta:.2f}%", ln=True)
        pdf.cell(200, 8, f"Margem Liquida: {margem_liquida:.2f}%", ln=True)

        pdf.output("relatorio_dre.pdf")

        with open("relatorio_dre.pdf", "rb") as file:
            st.download_button(
                label="Baixar PDF",
                data=file,
                file_name="relatorio_dre.pdf",
                mime="application/pdf"
            )

