import os
import re
import streamlit as st
import pandas as pd
import bcrypt

pd.options.display.float_format = "{:,.2f}".format

# =========================
# CONFIGURAÇÃO DO APP
# =========================
st.set_page_config(page_title="Consulta Clientes Pirâmide Q425", layout="centered")

# =========================
# SECRETS LOADER (Render / env safe)
# =========================
def load_auth_from_env():
    s = os.environ.get("STREAMLIT_SECRETS")
    if not s:
        return None
    try:
        import tomllib as _toml  # Python 3.11+
        parsed = _toml.loads(s)
    except Exception:
        try:
            import toml as _toml  # pip install toml
            parsed = _toml.loads(s)
        except Exception as e:
            print("Erro ao parsear STREAMLIT_SECRETS:", e)
            return None
    if isinstance(parsed, dict):
        return parsed.get("auth") or parsed
    return None

env_auth = load_auth_from_env()
if env_auth is not None:
    auth = env_auth
else:
    try:
        auth = st.secrets.get("auth", None)
    except Exception:
        auth = None

if not auth:
    st.error("Configuração de autenticação não encontrada. Verifique .streamlit/secrets.toml ou a variável STREAMLIT_SECRETS.")
    st.stop()

# =========================
# LOGIN
# =========================
usernames = auth.get("usernames", [])
hashed_passwords = auth.get("passwords", [])
names = auth.get("names", [])
users = {u: h.encode("utf-8") if isinstance(h, str) else str(h).encode("utf-8") for u, h in zip(usernames, hashed_passwords)}

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

# =========================
# CARREGAR PLANILHA
# =========================
DEFAULT_XLSX = "Piramide Q425.xlsx"

@st.cache_data(show_spinner=False)
def load_excel(path):
    return pd.read_excel(path)

if os.path.exists(DEFAULT_XLSX):
    try:
        df = load_excel(DEFAULT_XLSX)
        df.columns = df.columns.str.strip().str.upper()
    except Exception as e:
        st.error(f"Erro ao ler o arquivo '{DEFAULT_XLSX}': {e}")
        st.stop()
else:
    st.error(f"Arquivo '{DEFAULT_XLSX}' não encontrado na raiz do projeto.")
    st.stop()

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
    if termo.strip() == "":
        st.warning("Digite algo para buscar.")
    elif coluna not in df.columns:
        st.error(f"A coluna '{coluna}' não existe na planilha.")
    else:
        work = df.copy()

        if coluna in ["CNPJ", "COD_JC"]:
            def only_digits(s): return re.sub(r'\D', '', str(s))
            work[coluna + "_LIMPO"] = work[coluna].astype(str).apply(only_digits)
            termo_limpo = only_digits(termo)
            resultado = work[work[coluna + "_LIMPO"].str.contains(termo_limpo, na=False)]
        else:
            resultado = work[work[coluna].astype(str).str.contains(termo, case=False, na=False)]

        if resultado.empty:
            st.warning("Nenhum cliente encontrado.")
        else:
            st.success(f"{len(resultado)} resultado(s) encontrado(s).")

            # Cópia para exibição (sem alterar df original)
            display_df = resultado.copy()

            # Formatar números (2 casas decimais)
            numeric_cols = display_df.select_dtypes(include=["number"]).columns.tolist()
            if numeric_cols:
                display_df[numeric_cols] = display_df[numeric_cols].applymap(
                    lambda x: f"{x:,.2f}" if pd.notna(x) else ""
                )

            # Limpar CNPJ/COD_JC apenas para exibição
            for c in ["CNPJ", "COD_JC"]:
                if c in display_df.columns:
                    display_df[c] = display_df[c].astype(str).str.replace(r'[^0-9]', '', regex=True)

            # Seções de exibição
            principais1 = [c for c in ["RAZAO_SOCIAL", "CNPJ", "COD_JC", "FAIXA PEX", "FAIXA SORT", "DGTT"] if c in display_df.columns]
            principais2 = [c for c in ["AMBIENTE", "PERFIL", "GRUPO", "COLIGAÇÃO"] if c in display_df.columns]
            vendas1 = [c for c in ["POTENCIAL", "OPORT_AGO", "OPORT_SET", "MD_TRI_COLG", "REAL_MES_COLG"] if c in display_df.columns]
            vendas2 = [c for c in ["MD_TRI_3M", "REAL_MES_3M", "MD_TRI_JC", "REAL_MES_JC"] if c in display_df.columns]
            extras1 = [c for c in ["SEGMENTO", "CIDADE"] if c in display_df.columns]
            extras2 = [c for c in ["SUPERVISOR", "VENDEDOR"] if c in display_df.columns]

            # Exibição final (dados sem alteração)
            if principais1:
                st.subheader("Informações principais")
                st.dataframe(display_df[principais1], hide_index=True)
            if principais2:
                st.dataframe(display_df[principais2], hide_index=True)

            if vendas1:
                st.subheader("Resumo vendas")
                st.dataframe(display_df[vendas1], hide_index=True)
            if vendas2:
                st.dataframe(display_df[vendas2], hide_index=True)

            if extras1:
                st.subheader("Informações adicionais")
                st.dataframe(display_df[extras1], hide_index=True)
            if extras2:
                st.subheader("Gestores Comerciais")
                st.dataframe(display_df[extras2], hide_index=True)