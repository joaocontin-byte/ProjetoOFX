from io import BytesIO
import unicodedata

from ofxparse import OfxParser


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.upper())
    return "".join(letra for letra in texto if not unicodedata.combining(letra))


def categorizar_movimentacao(descricao, valor=None):
    """Aplica categorias adequadas aos tipos de lançamento identificados no histórico."""
    descricao = _normalizar(descricao)

    # Receitas e despesas comuns em extratos empresariais.
    if any(palavra in descricao for palavra in ("FOLHA", "PRO LABORE")):
        return "Folha de pagamento"
    if "SALARIO" in descricao:
        return "Salário" if valor is None or valor > 0 else "Folha de pagamento"
    if any(palavra in descricao for palavra in ("MATERIAL LIMPEZA", "PRODUTOS LIMPEZA")):
        return "Material de limpeza"
    if any(palavra in descricao for palavra in ("MATERIAL ESCRITORIO", "PAPELARIA")):
        return "Material de escritório"
    if any(palavra in descricao for palavra in ("ALUGUEL", "LOCACAO", "ESCRITORIO")):
        return "Aluguel e escritório"
    if any(palavra in descricao for palavra in ("ENERGIA", "ELETRICA", "AGUA", "GAS")):
        return "Energia e utilidades"
    if any(palavra in descricao for palavra in ("INTERNET", "TELEFONIA", "TELECOM")):
        return "Internet e telefonia"
    if any(palavra in descricao for palavra in ("ESTACIONAMENTO", "UBER", "COMBUSTIVEL", "PEDAGIO", "POSTO")):
        return "Transporte e estacionamento"
    if any(palavra in descricao for palavra in ("EQUIPAMENTO", "HARDWARE", "COMPRA TI", "INFORMATICA")):
        return "Equipamentos e TI"
    if any(palavra in descricao for palavra in ("CLOUD", "SOFTWARE", "ASSINATURA", "LICENCA", "HOSTING", "HOSPEDAGEM")):
        return "Software e serviços digitais"
    if any(palavra in descricao for palavra in ("MANUTENCAO", "REPARO", "CONSERTO")):
        return "Manutenção e reparos"
    if any(palavra in descricao for palavra in ("RECEBIMENTO", "CLIENTE", "CONTRATO", "PROJETO")):
        return "Recebimentos de clientes"

    # Categorias pessoais que já faziam parte do sistema.
    if any(palavra in descricao for palavra in ("SUPERMERCADO", "MERCADO", "RESTAURANTE", "LANCHONETE", "PADARIA", "IFOOD")):
        return "Alimentação"
    if any(palavra in descricao for palavra in ("FARMACIA", "DROGARIA", "HOSPITAL", "CLINICA")):
        return "Saúde"
    if any(palavra in descricao for palavra in ("NETFLIX", "SPOTIFY", "CINEMA", "STREAMING")):
        return "Lazer"
    if any(palavra in descricao for palavra in ("UBER", "99", "COMBUSTIVEL", "ESTACIONAMENTO")):
        return "Transporte"
    return "Outros"


def ler_ofx(conteudo):
    """Lê bytes de um OFX e devolve movimentações prontas para exibição e gravação."""
    ofx = OfxParser.parse(BytesIO(conteudo))
    transacoes = ofx.account.statement.transactions
    movimentacoes = []
    for transacao in transacoes:
        descricao = transacao.memo or getattr(transacao, "payee", None) or "Sem descrição"
        movimentacoes.append({
            "data": transacao.date.date(),
            "valor": transacao.amount,
            "descricao": descricao,
            "categoria": categorizar_movimentacao(descricao, transacao.amount),
        })
    return movimentacoes


def salvar_movimentacoes(movimentacoes):
    from conexao import conectar

    banco = conectar()
    try:
        with banco.cursor() as cursor:
            for item in movimentacoes:
                cursor.execute(
                    """
                    INSERT INTO movimentacoes
                    (data_movimentacao, valor, descricao, categoria)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (data_movimentacao, valor, descricao)
                    DO NOTHING
                    """,
                    (item["data"], item["valor"], item["descricao"], item["categoria"]),
                )
        banco.commit()
    except Exception:
        banco.rollback()
        raise
    finally:
        banco.close()
