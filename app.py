import streamlit as st

st.set_page_config(page_title="Motor de Diagnóstico Financeiro", layout="centered")

st.title("📊 Motor de Diagnóstico Financeiro")

st.header("Entrada de Dados")

receita = st.number_input("Receita Bruta", min_value=0.0)
impostos = st.number_input("Impostos", min_value=0.0)
custos_variaveis = st.number_input("Custos Variáveis", min_value=0.0)
custos_fixos = st.number_input("Custos Fixos", min_value=0.0)
despesas = st.number_input("Despesas Operacionais", min_value=0.0)
depreciacao = st.number_input("Depreciação", min_value=0.0)
juros = st.number_input("Juros", min_value=0.0)

if st.button("Analisar Empresa"):

    # Cálculos principais
    receita_liquida = receita - impostos
    lucro_bruto = receita_liquida - custos_variaveis
    ebitda = receita_liquida - custos_variaveis - custos_fixos - despesas
    margem_ebitda = (ebitda / receita_liquida * 100) if receita_liquida > 0 else 0

    margem_contribuicao = receita - custos_variaveis
    percentual_mc = (margem_contribuicao / receita * 100) if receita > 0 else 0
    ponto_equilibrio = custos_fixos / (percentual_mc / 100) if percentual_mc > 0 else 0

    # Valuation
    valuation_3x = ebitda * 3
    valuation_5x = ebitda * 5
    valuation_8x = ebitda * 8

    # Score Financeiro simples
    score = 0

    if margem_ebitda >= 20:
        score += 40
    elif margem_ebitda >= 10:
        score += 25
    else:
        score += 10

    if percentual_mc >= 40:
        score += 30
    elif percentual_mc >= 25:
        score += 20
    else:
        score += 10

    if ebitda > 0:
        score += 30
    else:
        score += 0

    st.header("📈 Resultados")

    st.write("Receita Líquida:", round(receita_liquida, 2))
    st.write("Lucro Bruto:", round(lucro_bruto, 2))
    st.write("EBITDA:", round(ebitda, 2))
    st.write("Margem EBITDA (%):", round(margem_ebitda, 2))
    st.write("Margem de Contribuição (%):", round(percentual_mc, 2))
    st.write("Ponto de Equilíbrio:", round(ponto_equilibrio, 2))

    st.header("💰 Valuation Estimado")

    st.write("Valuation Conservador (3x EBITDA):", round(valuation_3x, 2))
    st.write("Valuation Médio (5x EBITDA):", round(valuation_5x, 2))
    st.write("Valuation Agressivo (8x EBITDA):", round(valuation_8x, 2))

    st.header("🧠 Score Financeiro")

    st.progress(score / 100)
    st.write("Score da Empresa:", score, "/ 100")

    st.header("📌 Diagnóstico Automático")

    if margem_ebitda < 10:
        st.warning("Baixa eficiência operacional.")
    else:
        st.success("Boa eficiência operacional.")

    if percentual_mc < 25:
        st.warning("Margem de contribuição baixa. Rever precificação.")
    else:
        st.success("Boa margem de contribuição.")

    if ebitda <= 0:
        st.error("Empresa não está gerando resultado operacional positivo.")
