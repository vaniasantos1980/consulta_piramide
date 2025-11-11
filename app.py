import streamlit as st
import pandas as pd
pd.options.display.float_format = "{:,.2f}".format
import bcrypt
import re

# =========================
# CONFIGURAÇÃO DO APP
# =========================
st.set_page_config(page_title="Consulta Clientes Pirâmide Q425", layout="centered")

# =========================
# LER CONFIGURAÇÕES DO SECRETS
# =========================
# -- secrets loader (Render / environment safe) --
import os

def load_auth_from_env():
    """
    Lê a variável de ambiente STREAMLIT_SECRETS (conteúdo TOML).
    Retorna dicionário equivalente a st.secrets["auth"] se encontrado,
    ou None.
    """
    s = os.environ.get("STREAMLIT_SECRETS")
    if not s:
        return None

    # tenta usar tomllib (Python 3.11+), senão tenta a lib 'toml'
    try:
        import tomllib as _toml
        parsed = _toml.loads(s)
    except (ModuleNotFoundError, AttributeError):
        try:
            import toml as _toml  # pip install toml se necessário
            parsed = _toml.loads(s)
        except Exception as e:
            print("Erro ao parsear STREAMLIT_SECRETS:", e)
            return None

    auth = parsed.get("auth") if isinstance(parsed, dict) else None
    return auth

# usa env primeiro, senão st.secrets
env_auth = load_auth_from_env()
if env_auth is not None:
    auth = env_auth
else:
    auth = st.secrets.get("auth", None)

usernames = auth.get("usernames", [])
hashed_passwords = auth.get("passwords", [])
names = auth.get("names", [])

# Cria um dicionário usuário→hash
users = {u: h.encode("utf-8") for u, h in zip(usernames, hashed_passwords)}

# =========================
# LOGIN
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("🔐 Login de Acesso")

    username = st.text_input("Usuário:")
    password = st.text_input("Senha:", type="password")

    if st.button("Entrar"):
        if username in users:
            if bcrypt.checkpw(password.encode("utf-8"), users[username]):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login realizado com sucesso!")
                st.rerun()
            else:
                st.error("Senha incorreta.")
        else:
            st.error("Usuário não encontrado.")
    st.stop()

# =========================
# APP PRINCIPAL
# =========================
st.sidebar.success(f"Bem-vindo(a), {st.session_state.username}!")
if st.sidebar.button("Sair"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

st.title("📊 Consulta Clientes Pirâmide Q425")

@st.cache_data(show_spinner=False)
def load_excel(path):
    return pd.read_excel(path)

# --- início do bloco: carregar automaticamente a planilha da raiz ---
import os

DEFAULT_XLSX = "Piramide Q425.xlsx"  # nome do arquivo padrão

@st.cache_data(show_spinner=False)
def load_excel(path):
    return pd.read_excel(path)

# verifica se o arquivo existe na raiz do projeto
if os.path.exists(DEFAULT_XLSX):
    try:
        df = load_excel(DEFAULT_XLSX)

        # ✅ Formatando números com 2 casas decimais
        df = df.applymap(lambda x: round(x, 2) if isinstance(x, (int, float)) else x)

    except Exception as e:
        st.error(f"Erro ao ler o arquivo '{DEFAULT_XLSX}': {e}")
        st.stop()
else:
    st.error(f"Arquivo '{DEFAULT_XLSX}' não encontrado na raiz do projeto. Coloque o arquivo na pasta do app e reinicie.")
    st.stop()

# --- fim do bloco ---

# =========================
# BUSCA DE CLIENTES
# =========================
opcao = st.radio("Selecione o tipo de busca:", ("Razão Social", "CNPJ", "Código JC"))

if opcao == "Razão Social":
    termo = st.text_input("Digite a razão social:")
    coluna = "RAZAO_SOCIAL"
elif opcao == "CNPJ":
    termo = st.text_input("Digite o CNPJ (com ou sem formatação):")
    coluna = "CNPJ"
else:
    termo = st.text_input("Digite o código JC:")
    coluna = "COD_JC"

if st.button("Buscar"):
    if termo == "":
        st.warning("Digite algo para buscar.")
    elif coluna not in df.columns:
        st.error(f"A coluna '{coluna}' não existe na planilha.")
    else:
        if coluna in ["CNPJ", "COD_JC"]:
            def only_digits(s): return re.sub(r'\D', '', str(s))
            df[coluna + "_LIMPO"] = df[coluna].astype(str).apply(only_digits)
            termo_limpo = only_digits(termo)
            resultado = df[df[coluna + "_LIMPO"].str.contains(termo_limpo, na=False)]
        else:
            resultado = df[df[coluna].astype(str).str.contains(termo, case=False, na=False)]

        if resultado.empty:
            st.warning("Nenhum cliente encontrado.")
        else:
            st.success(f"{len(resultado)} resultado(s) encontrado(s).")

            principais1 = [c for c in ["RAZAO_SOCIAL", "CNPJ", "COD_JC", "FAIXA PEX", "FAIXA SORT", "DGTT"] if c in resultado.columns]
            principais2 = [c for c in ["AMBIENTE", "PERFIL", "GRUPO", "COLIGAÇÃO"] if c in resultado.columns]
            vendas1 = [c for c in ["POTENCIAL", "OPORT_AGO", "OPORT_SET", "MD_TRI_COLG", "REAL_MES_COLG"] if c in resultado.columns]
            vendas2 = [c for c in ["MD_TRI_3M", "REAL_MES_3M", "MD_TRI_JC", "REAL_MES_JC"] if c in resultado.columns]
            extras1 = [c for c in ["SEGMENTO", "CIDADE"] if c in resultado.columns]
            extras2 = [c for c in ["SUPERVISOR", "VENDEDOR"] if c in resultado.columns]

            if principais1:
                st.subheader("Informações principais")
                st.dataframe(resultado[principais1], hide_index=True)
            if principais2:        
                st.dataframe(resultado[principais2], hide_index=True)
            
            if vendas1:
                st.subheader("Resumo vendas")
                st.dataframe(resultado[vendas1], hide_index=True)
            if vendas2:        
                st.dataframe(resultado[vendas2], hide_index=True)

            if extras1:
                st.subheader("Informações adicionais")
                st.dataframe(resultado[extras1], hide_index=True)
            if extras2:
                st.subheader("Gestores Comerciais")
                st.dataframe(resultado[extras2], hide_index=True)