import streamlit as st
import sqlite3
import hashlib
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Motor Financeiro SaaS", layout="wide")

# ==========================================
# BANCO DE DADOS
# ==========================================
conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# -------- TABELA USUÁRIOS --------
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT UNIQUE,
    senha TEXT,
    plano TEXT
)
""")

# -------- TABELA EMPRESAS --------
cursor.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    nome_empresa TEXT,
    cnpj TEXT,
    cidade TEXT,
    estado TEXT,
    data_criacao TEXT
)
""")

# -------- TABELA DRE --------
cursor.execute("""
CREATE TABLE IF NOT EXISTS dre (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    receita REAL,
    custos REAL,
    despesas REAL,
    impostos REAL,
    data TEXT
)
""")

conn.commit()

# ==========================================
# CRIAR ADMIN AUTOMÁTICO
# ==========================================
cursor.execute("SELECT * FROM usuarios WHERE email='admin@motorfinanceiro.com'")
admin_existe = cursor.fetchone()

if not admin_existe:
    senha_admin = hashlib.sha256("123456".encode()).hexdigest()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, plano) VALUES (?, ?, ?, ?)",
        ("Administrador", "admin@motorfinanceiro.com", senha_admin, "admin")
    )
    conn.commit()

# ==========================================
# FUNÇÕES
# ==========================================
def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def criar_usuario(nome, email, senha):
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha, plano) VALUES (?, ?, ?, ?)",
            (nome, email, hash_senha(senha), "pendente")
        )
        conn.commit()
        return True
    except:
        return False

def autenticar(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email=? AND senha=?",
        (email, hash_senha(senha))
    )
    return cursor.fetchone()

# ==========================================
# SESSION
# ==========================================
if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# ==========================================
# LOGIN / CADASTRO
# ==========================================
if not st.session_state.logado:

    st.title("🔐 Motor Financeiro SaaS")

    opcao = st.radio("Acesso", ["Login", "Criar Conta"])

    # -------- CRIAR CONTA --------
    if opcao == "Criar Conta":

        nome = st.text_input("Nome")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")

        if st.button("Cadastrar"):
            if criar_usuario(nome, email, senha):
                st.success("Conta criada! Aguarde aprovação do administrador.")
            else:
                st.error("Email já cadastrado.")

    # -------- LOGIN --------
    if opcao == "Login":

        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            usuario = autenticar(email, senha)

            if usuario:
                if usuario[4] in ["admin", "aprovado"]:
                    st.session_state.logado = True
                    st.session_state.usuario = usuario
                    st.rerun()
                else:
                    st.warning("⏳ Aguardando aprovação do administrador.")
            else:
                st.error("Email ou senha inválidos.")

# ==========================================
# SISTEMA LOGADO
# ==========================================
else:

    usuario = st.session_state.usuario
    usuario_id = usuario[0]
    plano = usuario[4]

    st.sidebar.write(f"👤 {usuario[1]}")
    st.sidebar.write(f"Plano: {plano}")

    menu = ["Nova Empresa", "Histórico"]

    if plano == "admin":
        menu.append("Painel Admin")

    escolha = st.sidebar.selectbox("Menu", menu)

    # ==========================================
    # NOVA EMPRESA
    # ==========================================
    if escolha == "Nova Empresa":

        st.title("🏢 Cadastrar Empresa")

        nome_empresa = st.text_input("Nome da empresa")
        cnpj = st.text_input("CNPJ")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")

        if st.button("Salvar Empresa"):
            cursor.execute("""
                INSERT INTO empresas (usuario_id, nome_empresa, cnpj, cidade, estado, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (usuario_id, nome_empresa, cnpj, cidade, estado, datetime.now()))
            conn.commit()
            st.success("Empresa cadastrada com sucesso!")

        st.divider()
        st.subheader("📊 Inserir DRE")

        receita = st.number_input("Receita", min_value=0.0)
        custos = st.number_input("Custos", min_value=0.0)
        despesas = st.number_input("Despesas", min_value=0.0)
        impostos = st.number_input("Impostos", min_value=0.0)

        if st.button("Salvar DRE"):
            cursor.execute("""
                SELECT id FROM empresas
                WHERE usuario_id=?
                ORDER BY id DESC LIMIT 1
            """, (usuario_id,))
            empresa = cursor.fetchone()

            if empresa:
                cursor.execute("""
                    INSERT INTO dre (empresa_id, receita, custos, despesas, impostos, data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (empresa[0], receita, custos, despesas, impostos, datetime.now()))
                conn.commit()
                st.success("DRE salva com sucesso!")
            else:
                st.error("Cadastre uma empresa primeiro.")

    # ==========================================
    # HISTÓRICO
    # ==========================================
    if escolha == "Histórico":

        st.title("📈 Histórico Financeiro")

        cursor.execute("""
            SELECT dre.receita, dre.custos, dre.despesas, dre.impostos, dre.data
            FROM dre
            JOIN empresas ON dre.empresa_id = empresas.id
            WHERE empresas.usuario_id=?
        """, (usuario_id,))

        dados = cursor.fetchall()

        if dados:
            df = pd.DataFrame(dados, columns=["Receita", "Custos", "Despesas", "Impostos", "Data"])
            df["Lucro"] = df["Receita"] - df["Custos"] - df["Despesas"] - df["Impostos"]

            st.dataframe(df)

            fig = px.line(df, x="Data", y="Lucro")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhum registro encontrado.")

    # ==========================================
    # PAINEL ADMIN
    # ==========================================
    if escolha == "Painel Admin":

        st.title("🛠 Painel Administrativo")

        cursor.execute("SELECT id, nome, email, plano FROM usuarios")
        usuarios = cursor.fetchall()

        df = pd.DataFrame(usuarios, columns=["ID", "Nome", "Email", "Plano"])
        st.dataframe(df)

        user_id = st.number_input("ID do usuário", step=1)

        col1, col2 = st.columns(2)

        if col1.button("Aprovar Usuário"):
            cursor.execute("UPDATE usuarios SET plano='aprovado' WHERE id=?", (user_id,))
            conn.commit()
            st.success("Usuário aprovado!")

        if col2.button("Tornar Admin"):
            cursor.execute("UPDATE usuarios SET plano='admin' WHERE id=?", (user_id,))
            conn.commit()
            st.success("Usuário agora é admin!")

    # ==========================================
    # LOGOUT
    # ==========================================
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
