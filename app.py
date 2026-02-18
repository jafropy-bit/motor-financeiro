import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Motor Financeiro", layout="wide")

st.title("🚀 Motor Financeiro Empresarial")
st.markdown("Sistema de análise financeira, DRE completo e valuation por empresa.")

# -------------------------------
# CONEXÃO COM BANCO
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
    deducoes REAL,
    custos REAL,
    despesas_adm REAL,
    despesas_comerciais REAL,
    depreciacao REAL,
    resultado_financeiro REAL,
    impostos REAL,
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

    submitted_empresa = st.form_submit_button("Salvar Empresa")

    if submitted_empresa:
        cursor.execute(
            "INSERT INTO empresas (nome, cnpj, data_fundacao, area_atuacao) VALUES (?, ?, ?, ?)",
            (nome, cnpj, str(data_fundacao), area_atuacao)
        )
        conn.commit()
        st.success("Empresa cadastrada com sucesso!")

st.markdown("---")

# -------------------------------
# SELECIONAR EMPRESA
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
# FORMULÁRIO DRE COMPLETO
# -------------------------------

st.subheader("📊 Inserir DRE")

with st.form("form_dre"):

    receita_bruta = st.number_input("Receita Bruta", min_value=0.0)
    deducoes = st.number_input("Deduções / Impostos sobre Receita", min_value=0.0)
    custos = st.number_input("Custos (CMV/CPV/CSP)", min_value=0.0)
    despesas_adm = st.number_input("Despesas Administrativas", min_value=0.0)
    despesas_comerciais = st.number_input("Despesas Comerciais", min_value=0.0)
    depreciacao = st.number_input("Depreciação / Amortização", min_value=0.0)
    resultado_financeiro = st.number_input("Resultado Financeiro", min_value=0.0)
    impostos = st.number_input("Impostos sobre Lucro", min_value=0.0)

    submitted_dre = st.form_submit_button("Salvar DRE")

    if submitted_dre:
        cursor.execute("""
        INSERT INTO dados_financeiros 
        (empresa_id, receita_bruta, deducoes, custos, despesas_adm, despesas_comerciais,
         depreciacao, resultado_financeiro, impostos, data_registro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            empresa_id,
            receita_bruta,
            deducoes,
            custos,
            despesas_adm,
            despesas_comerciais,
            depreciacao,
            resultado_financeiro,
            impostos,
            str(datetime.now())
        ))
        conn.commit()
        st.success("DRE salvo com sucesso!")

st.markdown("---")

# -------------------------------
# BUSCAR ÚLTIMO DRE
# -------------------------------

cursor.execute("""
SELECT receita_bruta, deducoes, custos, despesas_adm, despesas_comerciais,
       depreciacao, resultado_financeiro, impostos
FROM dados_financeiros
WHERE empresa_id = ?
ORDER BY id DESC
LIMIT 1
""", (empresa_id,))

dados = cursor.fetchone()

if dados:

    receita_bruta, deducoes, custos, despesas_adm, despesas_comerciais, depreciacao, resultado_financeiro, impostos = dados

    # -------------------------------
    # CÁLCULO DO DRE
    # -------------------------------

    receita_liquida = receita_bruta - deducoes
    lucro_bruto = receita_liquida - custos

    despesas_operacionais = despesas_adm + despesas_comerciais
    ebitda = lucro_bruto - despesas_operacionais

    ebit = ebitda - depreciacao
    lucro_antes_ir = ebit + resultado_financeiro
    lucro_liquido = lucro_antes_ir - impostos

    # -------------------------------
    # EXIBIÇÃO DO DRE
    # -------------------------------

    st.subheader("📑 Demonstração do Resultado (DRE)")

    st.write(f"Receita Bruta: R$ {receita_bruta:,.2f}")
    st.write(f"(-) Deduções: R$ {deducoes:,.2f}")
    st.write(f"= Receita Líquida: R$ {receita_liquida:,.2f}")

    st.write(f"(-) Custos: R$ {custos:,.2f}")
    st.write(f"= Lucro Bruto: R$ {lucro_bruto:,.2f}")

    st.write(f"(-) Despesas Operacionais: R$ {despesas_operacionais:,.2f}")
    st.write(f"= EBITDA: R$ {ebitda:,.2f}")

    st.write(f"(-) Depreciação: R$ {depreciacao:,.2f}")
    st.write(f"= EBIT: R$ {ebit:,.2f}")

    st.write(f"(+) Resultado Financeiro: R$ {resultado_financeiro:,.2f}")
    st.write(f"= Lucro Antes do IR: R$ {lucro_antes_ir:,.2f}")

    st.write(f"(-) Impostos: R$ {impostos:,.2f}")
    st.write(f"= Lucro Líquido: R$ {lucro_liquido:,.2f}")

    st.markdown("---")

    # -------------------------------
    # VALUATION
    # -------------------------------

    st.subheader("💰 Valuation Estimado")

    st.write(f"Valuation Conservador (3x EBITDA): R$ {ebitda * 3:,.2f}")
    st.write(f"Valuation Médio (5x EBITDA): R$ {ebitda * 5:,.2f}")
    st.write(f"Valuation Agressivo (8x EBITDA): R$ {ebitda * 8:,.2f}")

else:
    st.info("Ainda não há DRE cadastrado para esta empresa.")
