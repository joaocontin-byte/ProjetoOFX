# Projeto OFX - Leitura de Extratos Bancários com Python

## Sobre o projeto

Este projeto foi desenvolvido para realizar a leitura de arquivos OFX (Open Financial Exchange), utilizados em extratos bancários. O programa utiliza Python para ler as movimentações financeiras, calcular os totais de entradas e saídas e armazenar os dados em um banco de dados PostgreSQL hospedado no Neon.

## Funcionalidades

- Leitura de arquivos OFX.
- Exibição das movimentações financeiras.
- Cálculo do total de entradas e saídas.
- Cálculo do saldo das movimentações.
- Armazenamento dos dados no PostgreSQL.
- Prevenção de registros duplicados no banco de dados.

## Tecnologias utilizadas

- **Python:** processamento dos arquivos OFX.
- **PostgreSQL:** armazenamento das movimentações financeiras.
- **Neon:** hospedagem do banco de dados PostgreSQL.
- **Psycopg2:** conexão entre Python e PostgreSQL.
- **Python-dotenv:** gerenciamento das variáveis de ambiente.
- **Git e GitHub:** versionamento e armazenamento do código-fonte.

## Estrutura do projeto

```text
ProjetoOFX/
├── main.py
├── conexao.py
├── teste_conexao.py
├── .gitignore
├── .env
├── extrato.ofx
└── README.md
```

Os arquivos `.env`, `extrato.ofx` e a pasta do ambiente virtual não devem ser enviados ao GitHub quando contiverem credenciais ou dados privados.

## Como executar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/joaocontin-byte/ProjetoOFX.git
```

### 2. Entrar na pasta do projeto

```bash
cd ProjetoOFX
```

### 3. Criar um ambiente virtual

```bash
python -m venv venv
```

### 4. Ativar o ambiente virtual

No Windows:

```bash
venv\Scripts\activate
```

### 5. Instalar as dependências

```bash
pip install psycopg2-binary python-dotenv
```

### 6. Configurar a conexão com o banco de dados

Crie um arquivo `.env` na pasta do projeto e adicione a variável de conexão:

```env
DATABASE_URL="SUA_STRING_DE_CONEXAO_DO_NEON"
```

Substitua o texto de exemplo pela string de conexão do seu banco Neon. Não compartilhe esse arquivo publicamente.

### 7. Executar o programa

```bash
python main.py
```

## Banco de dados

Os dados são armazenados em uma tabela chamada `movimentacoes`, que contém as seguintes informações:

| Campo | Descrição |
|---|---|
| `id` | Identificador da movimentação |
| `data_movimentacao` | Data da movimentação |
| `valor` | Valor da movimentação |
| `descricao` | Descrição da movimentação |

O projeto também possui uma restrição para evitar a inserção de movimentações duplicadas.

## Resultado esperado

Na execução realizada durante o desenvolvimento, o programa processou 15 movimentações financeiras, apresentando os seguintes resultados:

- **Entradas:** R$ 17.900,00
- **Saídas:** R$ -6.059,70
- **Saldo:** R$ 11.840,30

Os valores acima correspondem ao arquivo OFX utilizado nos testes.

## Objetivo acadêmico

O objetivo deste projeto é praticar a leitura e o processamento de arquivos com Python, a conexão com bancos de dados PostgreSQL e o armazenamento de informações financeiras, utilizando ferramentas de versionamento de código.

## Autor

João Contin

Repositório: https://github.com/joaocontin-byte/ProjetoOFX
