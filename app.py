import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Motor Financeiro", layout="wide")

# =============================
# CONEXÃO
# =============================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

# =============================
# CRIA TABELAS
# =============================

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
    receita REAL,
    lucro REAL,
    data TEXT
)
""")

conn.commit()

# =============================
# GARANTE ADMIN
# =============================

cursor.execute("SELECT * FROM usuarios WHERE email=?", ("admin@motorfinanceiro.com",))
if not cursor.fetchone():
    senha_admin = hashlib.sha256("admin123".encode()).hexdigest()
    cursor.execute(
        "INSERT INTO usuarios (nome,email,senha,plano) VALUES (?,?,?,?)",
        ("Administrador","admin@motorfinanceiro.com",senha_admin,"admin")
    )
    conn.commit()

# =============================
# FUNÇÕES
# =============================

def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()

def login(email, senha):
    cursor.execute(
        "SELECT * FROM usuarios WHERE email=? AND senha=?",
        (email, hash_senha(senha))
    )
    return cursor.fetchone()

def cadastrar(nome,email,senha):
    try:
        cursor.execute(
            "INSERT INTO usuarios (nome,email,senha,plano) VALUES (?,?,?,?)",
            (nome,email,hash_senha(senha),"free")
        )
        conn.commit()
        return True
    except:
        return False

# =============================
# CONTROLE PÁGINA
# =============================

if "pagina" not in st.session_state:
    st.session_state.pagina = 1

# =============================
# BOTÃO ADMIN
# =============================

col1,col2 = st.columns([9,1])
with col2:
    if st.button("Admin"):
        st.session_state.pagina="admin"

# =============================
# PÁGINA 1 - EMPRESA
# =============================

if st.session_state.pagina==1:
    st.title("Cadastro Empresa")
    nome_empresa=st.text_input("Nome Empresa")
    if st.button("Próxima"):
        st.session_state.nome_empresa=nome_empresa
        st.session_state.pagina=2
        st.rerun()

# =============================
# PÁGINA 2 - FINANCEIRO
# =============================

elif st.session_state.pagina==2:
    st.title("Financeiro")
    receita=st.number_input("Receita",0.0)
    custos=st.number_input("Custos",0.0)
    despesas=st.number_input("Despesas",0.0)
    impostos=st.number_input("Impostos",0.0)

    if st.button("Ir para Cadastro/Login"):
        st.session_state.financeiro={
            "receita":receita,
            "custos":custos,
            "despesas":despesas,
            "impostos":impostos
        }
        st.session_state.pagina=3
        st.rerun()

# =============================
# PÁGINA 3 - CADASTRO + LOGIN
# =============================

elif st.session_state.pagina==3:

    st.title("Cadastro ou Login")

    aba=st.radio("Escolha",["Cadastrar","Login"])

    if aba=="Cadastrar":
        nome=st.text_input("Nome")
        email=st.text_input("Email")
        senha=st.text_input("Senha",type="password")

        if st.button("Criar Conta"):
            if cadastrar(nome,email,senha):
                st.success("Conta criada! Faça login.")
            else:
                st.error("Email já existe")

    if aba=="Login":
        email=st.text_input("Email")
        senha=st.text_input("Senha",type="password")

        if st.button("Entrar"):
            usuario=login(email,senha)
            if usuario:
                st.session_state.usuario=usuario
                st.session_state.pagina=4
                st.rerun()
            else:
                st.error("Acesso negado")

# =============================
# PÁGINA 4 - RESULTADO
# =============================

elif st.session_state.pagina==4:

    dados=st.session_state.financeiro
    usuario=st.session_state.usuario

    receita=dados["receita"]
    lucro=receita-dados["custos"]-dados["despesas"]-dados["impostos"]

    st.subheader("Resultado")
    st.write("Receita:",receita)
    st.write("Lucro:",lucro)

    cursor.execute(
        "INSERT INTO empresas (usuario_id,nome_empresa,receita,lucro,data) VALUES (?,?,?,?,?)",
        (usuario[0],st.session_state.nome_empresa,receita,lucro,datetime.now().strftime("%d/%m/%Y"))
    )
    conn.commit()

# =============================
# PAINEL ADMIN
# =============================

elif st.session_state.pagina=="admin":

    st.title("Painel Admin")

    email=st.text_input("Email Admin")
    senha=st.text_input("Senha Admin",type="password")

    if st.button("Entrar Admin"):
        usuario=login(email,senha)
        if usuario and usuario[4]=="admin":
            st.success("Admin logado")

            st.subheader("Usuários")
            st.dataframe(pd.read_sql_query("SELECT id,nome,email,plano FROM usuarios",conn))

            st.subheader("Alterar Plano")
            user_id=st.number_input("ID usuário",step=1)
            plano=st.selectbox("Plano",["free","pago"])

            if st.button("Atualizar"):
                cursor.execute("UPDATE usuarios SET plano=? WHERE id=?",(plano,user_id))
                conn.commit()
                st.success("Plano atualizado")

        else:
            st.error("Acesso negado")
