# regen_hashes.py
import os
import sys
import bcrypt
import getpass
import secrets

# tenta usar tomllib (py3.11+), se não, usa pacote toml (instale com pip install toml)
try:
    import tomllib as toml_load
    def load_toml_bytes(b): return toml_load.loads(b.decode("utf-8"))
except Exception:
    try:
        import toml as toml_pkg
        def load_toml_bytes(b): return toml_pkg.loads(b.decode("utf-8"))
    except Exception:
        print("Erro: nenhum parser TOML disponível. Instale 'toml' ou use Python 3.11+.")
        sys.exit(1)

SECRETS_DIR = ".streamlit"
SECRETS_PATH = os.path.join(SECRETS_DIR, "secrets.toml")

def read_existing():
    if not os.path.exists(SECRETS_PATH):
        return {}
    with open(SECRETS_PATH, "rb") as f:
        content = f.read()
    try:
        data = load_toml_bytes(content)
        return data
    except Exception as e:
        print("Erro ao ler .streamlit/secrets.toml:", e)
        sys.exit(1)

def ask_passwords(usernames):
    print("\nVou pedir a senha para cada username. A senha será lida localmente (oculta) e será gerado um hash bcrypt.")
    print("Se quiser pular um usuário, pressione ENTER (será ignorado).")
    hashes = []
    provided_usernames = []
    for u in usernames:
        prompt = f"Senha para '{u}': "
        pwd = getpass.getpass(prompt)
        if not pwd:
            print(f"Ignorando usuário '{u}' (senha vazia).")
            continue
        h = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt())
        hashes.append(h.decode("utf-8"))
        provided_usernames.append(u)
    return provided_usernames, hashes

def write_secrets(new_auth_block):
    os.makedirs(SECRETS_DIR, exist_ok=True)
    # montar conteúdo TOML manualmente (simples e previsível)
    lines = []
    lines.append("[auth]\n")
    # names
    names = new_auth_block.get("names", [])
    lines.append("names = [")
    lines.append(", ".join(f'"{n}"' for n in names))
    lines.append("]\n")
    # usernames
    usernames = new_auth_block.get("usernames", [])
    lines.append("usernames = [")
    lines.append(", ".join(f'"{u}"' for u in usernames))
    lines.append("]\n")
    # passwords
    pw = new_auth_block.get("passwords", [])
    lines.append("passwords = [\n")
    for p in pw:
        lines.append(f'  "{p}",\n')
    lines.append("]\n")
    # cookie_name, key, cookie_expiry_days
    lines.append(f'cookie_name = "{new_auth_block.get("cookie_name","consulta_piramide_cookie")}"\n')
    lines.append(f'key = "{new_auth_block.get("key")}"\n')
    lines.append(f'cookie_expiry_days = {int(new_auth_block.get("cookie_expiry_days",30))}\n')

    with open(SECRETS_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"\nArquivo atualizado salvo em: {SECRETS_PATH}")

def main():
    existing = read_existing()
    auth = existing.get("auth", {}) if isinstance(existing, dict) else {}
    existing_names = auth.get("names", [])
    existing_usernames = auth.get("usernames", [])

    if not existing_usernames:
        print("Nenhuma lista 'usernames' encontrada em .streamlit/secrets.toml.")
        print("Por favor, edite .streamlit/secrets.toml e inclua a lista 'usernames' e 'names' antes de executar este script.")
        sys.exit(1)

    print("Usuários detectados no secrets.toml (na ordem):")
    for u in existing_usernames:
        print(" -", u)

    # pedir senha para cada username (na mesma ordem)
    provided_usernames, hashes = ask_passwords(existing_usernames)

    if not hashes:
        print("Nenhum hash gerado. Saindo sem alterações.")
        sys.exit(0)

    # preparar bloco novo
    new_key = secrets.token_urlsafe(32)
    new_auth = {
        "names": existing_names,  # mantemos os nomes existentes
        "usernames": existing_usernames,
        "passwords": hashes,
        "cookie_name": auth.get("cookie_name","consulta_piramide_cookie"),
        "key": new_key,
        "cookie_expiry_days": auth.get("cookie_expiry_days",30)
    }

    # mostrar resumo e confirmação
    print("\nResumo:")
    print(" - Usuários (contagem):", len(new_auth["usernames"]))
    print(" - Hashes gerados (contagem):", len(new_auth["passwords"]))
    print(" - Nova key (copiada para secrets):", new_key)
    confirm = input("Confirmar sobrescrever .streamlit/secrets.toml com esses valores? (s/N): ").strip().lower()
    if confirm != "s":
        print("Operação cancelada pelo usuário.")
        sys.exit(0)

    write_secrets(new_auth)
    print("Feito. Reinicie seu app Streamlit: streamlit run app.py")

if __name__ == "__main__":
    main()