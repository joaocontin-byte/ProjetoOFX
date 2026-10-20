
from conexao import conectar

try:
    banco = conectar()

    cursor = banco.cursor()
    cursor.execute("SELECT 1")

    resultado = cursor.fetchone()

    print("Conexão com o Neon realizada com sucesso!")
    print("Resultado do teste:", resultado[0])

    cursor.close()
    banco.close()

except Exception as erro:
    print("Erro ao conectar com o Neon:")
    print(erro)
