import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Motor Financeiro", layout="wide")

st.title("🚀 Motor Financeiro Empresarial")
st.markdown("Sistema de análise financeira, diagnóstico e valuation por empresa.")

# -------------------------------
# CONEXÃO COM BANCO DE DADOS
# -------------------------------

conn = sqlite3.connect("empresas.db", check_same_thread=False)
cursor = conn.cursor()

# -------------------------------
# CRIAÇÃO DAS TABELAS
# -------------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cnpj TEXT,
    data_fundacao TEXT,
    area_atuacao TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS dados_financeiros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    receita_bruta REAL,
    custos REAL,
    despesas REAL,
    data_registro TEXT,
    FOREIGN KEY (empresa_id) REFERENCES empresas (id)
)
""")

conn.commit()

# -------------------------------
# CADASTRO DE EMPRESA
# -------------------------------

st.subheader("🏢 Cadastro de Empresa")

with st.form("form_empresa"):
    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    data_fundacao = st.date_input("Data de Fundação")
    area_atuacao = st.selectbox(
        "Área de Atuação",
        [
            "Indústria",
            "Comércio",
            "Serviços",
            "Tecnologia",
            "Saúde",
            "Educação",
            "Construção",
            "Agronegócio",
            "Financeiro",
            "Outro"
        ]
    )

    submitted = st.form_submit_button("Salvar Empresa")

    if submitted:
        cursor.execute(
            "INSERT INTO empresas (nome, cnpj, data_fundacao, area_atuacao) VALUES (?, ?, ?, ?)",
            (nome, cnpj, str(data_fundacao), area_atuacao)
        )
        conn.commit()
        st.success("Empresa cadastrada com sucesso!")

st.markdown("---")

# -------------------------------
# SELEÇÃO DE EMPRESA
# -------------------------------

st.subheader("📋 Selecionar Empresa")

cursor.execute("SELECT id, nome FROM empresas")
empresas = cursor.fetchall()

if len(empresas) == 0:
    st.warning("Cadastre uma empresa primeiro.")
    st.stop()

empresa_dict = {empresa[1]: empresa[0] for empresa in empresas}

empresa_selecionada = st.selectbox(
    "Escolha a empresa",
    list(empresa_dict.keys())
)

empresa_id = empresa_dict[empresa_selecionada]

st.markdown("---")

# -------------------------------
# INSERIR DADOS FINANCEIROS
# -------------------------------

st.subheader("📊 Inserir Dados Financeiros")

with st.form("form_financeiro"):
    receita_bruta = st.number_input("Receita Bruta", min_value=0.0)
    custos = st.number_input("Custos", min_value=0.0)
    despesas = st.number_input("Despesas", min_value=0.0)

    submitted_fin = st.form_submit_button("Salvar Dados Financeiros")

    if submitted_fin:
        cursor.execute(
            """
            INSERT INTO dados_financeiros 
            (empresa_id, receita_bruta, custos, despesas, data_registro) 
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                empresa_id,
                receita_bruta,
                custos,
                despesas,
                str(datetime.now())
            )
        )
        conn.commit()
        st.success("Dados financeiros salvos com sucesso!")

st.markdown("---")

# -------------------------------
# EXIBIR ÚLTIMO REGISTRO FINANCEIRO
# -------------------------------

cursor.execute("""
SELECT receita_bruta, custos, despesas 
FROM dados_financeiros 
WHERE empresa_id = ? 
ORDER BY id DESC 
LIMIT 1
""", (empresa_id,))

dados = cursor.fetchone()

if dados:

    receita_bruta, custos, despesas = dados

    receita_liquida = receita_bruta
    lucro_bruto = receita_liquida - custos
    ebitda = lucro_bruto - despesas

    margem_ebitda = (ebitda / receita_liquida) * 100 if receita_liquida > 0 else 0
    margem_contribuicao = (lucro_bruto / receita_liquida) * 100 if receita_liquida > 0 else 0
    ponto_equilibrio = despesas / (margem_contribuicao / 100) if margem_contribuicao > 0 else 0

    st.subheader("📈 Resultados Financeiros")

    col1, col2, col3 = st.columns(3)

    col1.metric("Receita Líquida", f"R$ {receita_liquida:,.2f}")
    col2.metric("Lucro Bruto", f"R$ {lucro_bruto:,.2f}")
    col3.metric("EBITDA", f"R$ {ebitda:,.2f}")

    st.metric("Margem EBITDA (%)", f"{margem_ebitda:.2f}%")
    st.metric("Margem de Contribuição (%)", f"{margem_contribuicao:.2f}%")
    st.metric("Ponto de Equilíbrio", f"R$ {ponto_equilibrio:,.2f}")

    # Valuation simples
    st.subheader("💰 Valuation Estimado")

    st.write(f"Valuation Conservador (3x EBITDA): R$ {ebitda * 3:,.2f}")
    st.write(f"Valuation Médio (5x EBITDA): R$ {ebitda * 5:,.2f}")
    st.write(f"Valuation Agressivo (8x EBITDA): R$ {ebitda * 8:,.2f}")

else:
    st.info("Ainda não há dados financeiros cadastrados para esta empresa.")

