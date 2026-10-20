
from ofxparse import OfxParser
from conexao import conectar

# Função para categorizar as movimentações
def categorizar_movimentacao(descricao):
    descricao = descricao.upper()

    if any(palavra in descricao for palavra in [
        "SUPERMERCADO", "MERCADO", "RESTAURANTE",
        "LANCHONETE", "PADARIA", "IFOOD"
    ]):
        return "Alimentação"

    elif any(palavra in descricao for palavra in [
        "UBER", "99", "POSTO", "COMBUSTIVEL",
        "ESTACIONAMENTO"
    ]):
        return "Transporte"

    elif any(palavra in descricao for palavra in [
        "FARMACIA", "DROGARIA", "HOSPITAL", "CLINICA"
    ]):
        return "Saúde"

    elif any(palavra in descricao for palavra in [
        "NETFLIX", "SPOTIFY", "CINEMA", "STREAMING"
    ]):
        return "Lazer"

    elif any(palavra in descricao for palavra in [
        "SALARIO", "PAGAMENTO SALARIO"
    ]):
        return "Salário"

    else:
        return "Outros"


# 1. Ler o arquivo OFX
with open("extrato.ofx", "rb") as arquivo:
    ofx = OfxParser.parse(arquivo)

transacoes = ofx.account.statement.transactions

# 2. Calcular os totais
entradas = 0
saidas = 0

# 3. Conectar ao Neon
banco = conectar()
cursor = banco.cursor()

# 4. Exibir e salvar as movimentações
print("========== EXTRATO BANCÁRIO ==========")

for t in transacoes:
    data = t.date.date()
    valor = t.amount
    descricao = t.memo or "Sem descrição"

    # Identificar a categoria pela descrição
    categoria = categorizar_movimentacao(descricao)

    print(f"Data      : {t.date.strftime('%d/%m/%Y')}")
    print(f"Valor     : R$ {valor:.2f}")
    print(f"Descrição : {descricao}")
    print(f"Categoria : {categoria}")
    print("--------------------------------------")

    if valor > 0:
        entradas += valor
    elif valor < 0:
        saidas += valor

    # Salvar a movimentação no PostgreSQL
    cursor.execute(
        """
        INSERT INTO movimentacoes
        (data_movimentacao, valor, descricao, categoria)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (data_movimentacao, valor, descricao)
        DO NOTHING
        """,
        (data, valor, descricao, categoria)
    )

# 5. Confirmar as gravações
banco.commit()

# 6. Exibir o resumo
print("\n========== RESUMO DO EXTRATO ==========")
print(f"Quantidade de movimentações: {len(transacoes)}")
print(f"Total de entradas: R$ {entradas:.2f}")
print(f"Total de saídas: R$ {saidas:.2f}")
print(f"Saldo calculado: R$ {entradas + saidas:.2f}")

# 7. Encerrar a conexão
cursor.close()
banco.close()

print("\nMovimentações salvas no Neon com sucesso!")
