import streamlit as st
import sqlite3
import hashlib
import secrets
import string

st.set_page_config(page_title="Plataforma Financeira", layout="wide")

# ========================
# BANCO DE DADOS
# ========================

conn = sqlite3.connect("sistema.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    cnpj TEXT,
    pais_origem TEXT,
    pais_atuacao TEXT,
    email TEXT,
    telefone TEXT,
    whatsapp TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    email TEXT,
    senha TEXT,
    tipo TEXT
)
""")

conn.commit()

# ========================
# FUNÇÕES SEGURAS
# ========================

def gerar_hash(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha_digitada, senha_hash):
    return gerar_hash(senha_digitada) == senha_hash

def gerar_senha_automatica():
    caracteres = string.ascii_letters + string.digits + "!@#"
    return ''.join(secrets.choice(caracteres) for _ in range(10))

# ========================
# SESSION
# ========================

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.empresa_id = None
    st.session_state.tipo = None

# ========================
# FORMULÁRIO PÚBLICO
# ========================

def formulario_publico():
    st.title("Cadastro da Empresa")

    nome = st.text_input("Nome da Empresa")
    cnpj = st.text_input("CNPJ")
    pais_origem = st.text_input("País de Origem")

    pais_atuacao = st.selectbox(
        "País de Atuação",
        ["Brasil", "Estados Unidos", "Portugal", "Canadá"]
    )

    email = st.text_input("E-mail")
    telefone = st.text_input("Telefone Fixo (+País +DDD +Número)")
    whatsapp = st.text_input("WhatsApp (+País +DDD +Número)")

    if st.button("Enviar Cadastro"):
        cursor.execute("""
        INSERT INTO empresas
        (nome, cnpj, pais_origem, pais_atuacao, email, telefone, whatsapp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, cnpj, pais_origem, pais_atuacao, email, telefone, whatsapp, "pendente"))

        conn.commit()
        st.success("Cadastro enviado! Aguarde liberação de acesso.")

# ========================
# LOGIN CLIENTE
# ========================

def tela_login():
    st.title("Login Cliente")

    email = st.text_input("Email")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        cursor.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        usuario = cursor.fetchone()

        if usuario and verificar_senha(senha, usuario[3]):
            st.session_state.logado = True
            st.session_state.empresa_id = usuario[1]
            st.session_state.tipo = usuario[4]
            st.rerun()
        else:
            st.error("Credenciais inválidas")

# ========================
# PAINEL SUPER ADMIN
# ========================

def painel_admin():
    st.title("Painel Super Admin")

    cursor.execute("SELECT * FROM empresas WHERE status='pendente'")
    pendentes = cursor.fetchall()

    if not pendentes:
        st.info("Nenhuma empresa pendente.")
        return

    for empresa in pendentes:
        st.write("---")
        st.write(f"Empresa: {empresa[1]}")
        st.write(f"E-mail: {empresa[5]}")
        st.write(f"Telefone: {empresa[6]}")

        if st.button(f"Liberar {empresa[0]}"):
            senha_temp = gerar_senha_automatica()
            senha_hash = gerar_hash(senha_temp)

            cursor.execute("""
            INSERT INTO usuarios
            (empresa_id, email, senha, tipo)
            VALUES (?, ?, ?, ?)
            """, (empresa[0], empresa[5], senha_hash, "admin"))

            cursor.execute("""
            UPDATE empresas SET status='ativo' WHERE id=?
            """, (empresa[0],))

            conn.commit()

            st.success("Acesso liberado!")
            st.warning(f"Senha gerada: {senha_temp}")
            st.info("Envie essa senha ao cliente.")

# ========================
# DASHBOARD CLIENTE
# ========================

def dashboard_cliente():
    st.title("Área do Cliente")

    cursor.execute("""
    SELECT nome, cnpj, pais_origem, pais_atuacao
    FROM empresas WHERE id=?
    """, (st.session_state.empresa_id,))

    empresa = cursor.fetchone()

    if empresa:
        st.write("Empresa:", empresa[0])
        st.write("CNPJ:", empresa[1])
        st.write("País de Origem:", empresa[2])
        st.write("País de Atuação:", empresa[3])

    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()

# ========================
# SUPER ADMIN FIXO
# ========================

SUPER_ADMIN_EMAIL = "master@sistema.com"
SUPER_ADMIN_SENHA = "Master@123"

# ========================
# MENU
# ========================

menu = st.sidebar.selectbox("Menu", ["Cadastro Empresa", "Login", "Super Admin"])

if not st.session_state.logado:

    if menu == "Cadastro Empresa":
        formulario_publico()

    elif menu == "Login":
        tela_login()

    elif menu == "Super Admin":
        st.title("Acesso Super Admin")

        email = st.text_input("Email Admin")
        senha = st.text_input("Senha Admin", type="password")

        if st.button("Entrar Admin"):
            if email == SUPER_ADMIN_EMAIL and senha == SUPER_ADMIN_SENHA:
                painel_admin()
            else:
                st.error("Acesso negado")

else:
    dashboard_cliente()
