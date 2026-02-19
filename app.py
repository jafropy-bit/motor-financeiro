import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# ------------------------
# CONFIGURAÇÃO
# ------------------------
VERSAO = "FREE"  # Mude para PREMIUM para liberar tudo

st.title("📊 Motor Financeiro - Análise de DRE")

st.markdown("Insira os dados do seu DRE abaixo:")

# ------------------------
# INPUTS
# ------------------------

col1, col2 = st.columns(2)

with col1:
    receita = st.number_input("Receita Bruta", min_value=0.0)
    impostos = st.number_input("Impostos", min_value=0.0)
    custos = st.number_input("Custos", min_value=0.0)

with col2:
    despesas = st.number_input("Despesas Operacionais", min_value=0.0)
    depreciacao = st.number_input("Depreciação", min_value=0.0)
    juros = st.number_input("Juros", min_value=0.0)

# ------------------------
# CÁLCULOS
# ------------------------

if receita > 0:
    ebitda = receita - impostos - custos - despesas
    lucro_liquido = ebitda - depreciacao - juros
    
    margem_ebitda = (ebitda / receita) * 100
    margem_liquida = (lucro_liquido / receita) * 100
    
    # Score simples
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
    st.subheader("📈 Resultado")

    # ------------------------
    # VERSÃO FREE
    # ------------------------
    if VERSAO == "FREE":
        st.metric("Margem EBITDA", f"{margem_ebitda:.2f}%")
        
        st.warning("🔒 Sua margem está abaixo da média do mercado.")
        st.info("Libere o Premium para ver Score, gráficos e relatório em PDF.")

    # ------------------------
    # VERSÃO PREMIUM
    # ------------------------
    if VERSAO == "PREMIUM":

        col3, col4, col5 = st.columns(3)

        col3.metric("Margem EBITDA", f"{margem_ebitda:.2f}%")
        col4.metric("Margem Líquida", f"{margem_liquida:.2f}%")
        col5.metric("Score Financeiro", f"{score}/100")

        # GRÁFICO
        df = pd.DataFrame({
            "Indicador": ["Receita", "EBITDA", "Lucro Líquido"],
            "Valor": [receita, ebitda, lucro_liquido]
        })

        fig = px.bar(df, x="Indicador", y="Valor")
        st.plotly_chart(fig, use_container_width=True)

        # PDF
        if st.button("📄 Gerar Relatório PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            pdf.cell(200, 10, txt="Relatório Financeiro", ln=True)
            pdf.cell(200, 10, txt=f"Margem EBITDA: {margem_ebitda:.2f}%", ln=True)
            pdf.cell(200, 10, txt=f"Margem Líquida: {margem_liquida:.2f}%", ln=True)
            pdf.cell(200, 10, txt=f"Score: {score}/100", ln=True)

            pdf.output("relatorio.pdf")

            with open("relatorio.pdf", "rb") as file:
                st.download_button(
                    label="Baixar PDF",
                    data=file,
                    file_name="relatorio_financeiro.pdf",
                    mime="application/pdf"
                )

else:
    st.info("Insira a Receita para iniciar a análise.")
