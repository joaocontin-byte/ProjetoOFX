# Projeto OFX

Aplicação web para importar extratos OFX, categorizar movimentações, conferir entradas e saídas e salvar os lançamentos no PostgreSQL (Neon). A interface é feita em React e a API em FastAPI; as credenciais do banco permanecem no backend.

## Funcionalidades

- Envio de arquivo OFX pelo navegador e pré-visualização antes de salvar.
- Resumo de entradas, saídas, saldo e quantidade de movimentações.
- Busca e filtro por categoria.
- Exportação das movimentações exibidas em CSV, Excel (.xlsx) ou PDF, incluindo as categorias ajustadas.
- Sugestões dinâmicas de categorias com base nos nomes das despesas do OFX, sem selecionar nenhuma automaticamente.
- Escolha manual das sugestões ou criação de categorias próprias, disponíveis neste navegador nos próximos extratos.
- Salvamento no banco, ignorando lançamentos repetidos conforme a restrição de unicidade existente.
- Verificação da conexão com o banco pela interface.

## Pré-requisitos

- Python 3.10 ou superior.
- Node.js e npm.
- Uma tabela `movimentacoes` no PostgreSQL com `data_movimentacao`, `valor`, `descricao`, `categoria` e restrição `UNIQUE (data_movimentacao, valor, descricao)`.

## Configurar e iniciar

1. Configure a conexão do banco no arquivo `.env` na raiz:

   ```env
   DATABASE_URL="SUA_STRING_DE_CONEXAO_DO_NEON"
   ```

2. Instale as dependências Python e inicie a API, em um terminal na raiz do projeto:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn api:app --reload
   ```

3. Em outro terminal, também na raiz, instale as dependências do frontend e inicie o React:

   ```bash
   npm install
   npm run dev
   ```

4. Abra o endereço local mostrado pelo Vite (normalmente `http://localhost:5173`).

A API fica em `http://localhost:8000`; sua documentação interativa fica em `/docs`.

## Execução pelo terminal

O script `main.py` segue disponível para processar o arquivo `extrato.ofx` diretamente.

## Notas

Mantenha `.env` e extratos privados fora do Git. A API deve ser publicada em um serviço Python e o frontend em uma hospedagem estática para acesso público na internet; configure `VITE_API_URL` para o endereço da API e ajuste a origem CORS no `api.py` para o domínio do frontend.







