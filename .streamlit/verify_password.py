# verify_password.py
import os
import getpass
import bcrypt

# tenta carregar toml
try:
    import tomllib as toml_load  # python 3.11+
    def load_toml(path):
        with open(path, "rb") as f:
            return toml_load.loads(f.read().decode("utf-8"))
except Exception:
    import toml
    def load_toml(path):
        with open(path, "r", encoding="utf-8") as f:
            return toml.loads(f.read())

SECRETS_PATH = os.path.join(".streamlit", "secrets.toml")

if not os.path.exists(SECRETS_PATH):
    print("Arquivo .streamlit/secrets.toml não encontrado. Ajuste o caminho.")
    raise SystemExit(1)

data = load_toml(SECRETS_PATH)
auth = data.get("auth", {})
usernames = auth.get("usernames", [])
passwords = auth.get("passwords", [])

print("Usernames disponíveis:")
for u in usernames:
    print(" -", u)

user = input("\nDigite o username a testar (copie/cole da lista acima): ").strip()
if user not in usernames:
    print("Username não encontrado. Verifique capitalização/underscore. Saindo.")
    raise SystemExit(1)

pwd = getpass.getpass("Digite a senha em texto para testar: ")

idx = usernames.index(user)
try:
    hash_str = passwords[idx]
except Exception as e:
    print("Não foi possível obter o hash para esse usuário (índice inválido).")
    raise SystemExit(1)

# bcrypt expects bytes
try:
    ok = bcrypt.checkpw(pwd.encode("utf-8"), hash_str.encode("utf-8"))
except Exception as e:
    print("Erro ao verificar hash (formato inválido?):", e)
    raise SystemExit(1)

print("\nResultado:")
print(" - username:", user)
print(" - hash (preview):", hash_str[:20] + "..." if isinstance(hash_str, str) else str(hash_str))
print(" - senha confere:", ok)