import bcrypt

# copie e cole o hash exato do usuário "Teste" (primeiro da lista passwords)
hash_salvo = b"$2b$12$g5b/.n62RV2NW08qx6wkt0c3Dq1curleVgNbhdd1RjizjTv.ncqba"  # ← substitua se for diferente
senha_teste = "Teste123"

ok = bcrypt.checkpw(senha_teste.encode(), hash_salvo)
print("Senha confere:", ok)