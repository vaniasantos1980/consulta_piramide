# hash_passwords.py
import bcrypt
import getpass
import json

def main():
    print("Gerador de hashes bcrypt (para streamlit-authenticator)\n")
    users = []
    hashes = []
    while True:
        user = input("Digite o username para esse hash (ex: joao) ou ENTER para finalizar: ").strip()
        if user == "":
            break
        pwd = getpass.getpass(f"Digite a senha para '{user}': ")
        if not pwd:
            print("Senha vazia, ignorando esse usuário.")
            continue
        # gera hash bcrypt e decodifica para string
        hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())
        hashes.append(hashed.decode('utf-8'))
        users.append(user)

    if not hashes:
        print("Nenhuma senha informada. Saindo.")
        return

    print("\nUsuários gerados (ordem):")
    print(json.dumps(users, indent=2, ensure_ascii=False))
    print("\nCopie a lista abaixo (cada item é um hash bcrypt) e cole em st.secrets['auth']['passwords']:\n")
    print(json.dumps(hashes, indent=2, ensure_ascii=False))
    print("\nObservação: a ordem dos hashes corresponde à ordem dos usernames acima.")

if __name__ == "__main__":
    main()