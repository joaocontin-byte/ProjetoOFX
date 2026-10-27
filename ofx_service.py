from io import BytesIO
import unicodedata

from ofxparse import OfxParser


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.upper())
    return "".join(letra for letra in texto if not unicodedata.combining(letra))


def sugerir_categoria_despesa(descricao):
    """Sugere uma opção a partir do texto da despesa; não atribui a categoria."""
    descricao = _normalizar(descricao)
    regras = (
        (("FOLHA", "PRO LABORE", "PAGAMENTO SALARIO"), "Folha de pagamento"),
        (("MATERIAL LIMPEZA", "PRODUTOS LIMPEZA"), "Material de limpeza"),
        (("MATERIAL ESCRITORIO", "PAPELARIA"), "Material de escritório"),
        (("ALUGUEL", "LOCACAO", "ESCRITORIO"), "Aluguel e escritório"),
        (("ENERGIA", "ELETRICA", "AGUA", "GAS"), "Energia e utilidades"),
        (("INTERNET", "TELEFONIA", "TELECOM"), "Internet e telefonia"),
        (("ESTACIONAMENTO", "UBER", "COMBUSTIVEL", "PEDAGIO", "POSTO"), "Transporte e estacionamento"),
        (("EQUIPAMENTO", "HARDWARE", "COMPRA TI", "INFORMATICA"), "Equipamentos e TI"),
        (("CLOUD", "SOFTWARE", "ASSINATURA", "LICENCA", "HOSTING", "HOSPEDAGEM"), "Software e serviços digitais"),
        (("MANUTENCAO", "REPARO", "CONSERTO"), "Manutenção e reparos"),
        (("SUPERMERCADO", "MERCADO", "RESTAURANTE", "LANCHONETE", "PADARIA", "IFOOD"), "Alimentação"),
        (("FARMACIA", "DROGARIA", "HOSPITAL", "CLINICA"), "Saúde"),
        (("NETFLIX", "SPOTIFY", "CINEMA", "STREAMING"), "Lazer"),
    )
    for palavras, categoria in regras:
        if any(palavra in descricao for palavra in palavras):
            return categoria
    return None


def ler_ofx(conteudo):
    """Lê OFX sem atribuir categorias às movimentações."""
    ofx = OfxParser.parse(BytesIO(conteudo))
    transacoes = ofx.account.statement.transactions
    movimentacoes = []
    for transacao in transacoes:
        descricao = transacao.memo or getattr(transacao, "payee", None) or "Sem descrição"
        movimentacoes.append({
            "data": transacao.date.date(),
            "valor": transacao.amount,
            "descricao": descricao,
            "categoria": "",
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
