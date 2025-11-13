# Company RAG LangChain

Assistente RAG em FastAPI que responde perguntas usando documentos internos vetorizados em um banco Postgres com extensao pgvector. O pipeline usa LangChain (LLM GPT-4o-mini via OpenAI) e embeddings OpenAI para alimentar uma base vetorial `company_docs`.

## Fluxo de alto nivel
1. `ingest.py` carrega os PDFs da pasta `data/`, divide o texto em chunks (RecursiveCharacterTextSplitter, `chunk_size=800`, `chunk_overlap=150`) e grava embeddings no Postgres.
2. `app.py` expõe `/ask?q=...`, monta um chain LCEL com `PGVector.as_retriever()`, `ChatPromptTemplate` e `ChatOpenAI`.
3. O deploy preferencial usa `docker-compose.yml`, que sobe `rag-db` (pgvector/pg16) e `rag-api` (FastAPI).

## Preparacao do ambiente
1. **Variaveis**  
   Copie `.env.example` (ou crie `.env`) e defina:
   ```
   OPENAI_API_KEY=sk-...
   PG_CONNECTION=postgresql+psycopg://rag_user:rag_password@localhost:5432/rag_db
   ```
   Quando rodar em Docker, o `PG_CONNECTION` do container usa `db` como host (`...@db:5432/...`).  

2. **Execucao local**  
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   python ingest.py      # cria/atualiza embeddings
   uvicorn app:app --reload
   ```

3. **Execucao com Docker Compose**  
   ```powershell
   docker compose up --build -d
   docker compose exec api python ingest.py   # injeta PDFs no banco do container
   ```
   - `rag-api` exposto em `http://localhost:8000`.
   - `rag-db` exposto em `localhost:5432` (credenciais padrao `rag_user/rag_password`).

## Testando o endpoint
Com os containers (ou uvicorn) ativos:
```bash
curl "http://localhost:8000/ask?q=Quais%20multas%20se%20aplicam%20quando%20cancelo%20menos%20de%20uma%20semana%20antes%3F"
```
Resposta esperada:
```json
{
  "question": "...",
  "answer": "Quando voce cancela uma reserva menos de 7 dias antes da data de inicio, a multa integral e aplicada."
}
```

## Conteudo dos PDFs
### politicas_cancelamento.pdf
- **Prazos e janelas de cancelamento**  
  Reservas mensais podem ser canceladas sem custo ate 15 dias antes da data de inicio. Entre 14 e 7 dias ha multa de 30% do valor contratado; abaixo de 7 dias aplica-se a multa integral. Clientes premium podem remarcar ate duas vezes por trimestre sem multa, desde que avisem o gerente por escrito.
- **Fluxo operacional para registrar um cancelamento**  
  O atendente abre ticket no portal interno, anexa o e-mail do cliente e marca o motivo com categorias padrao. O financeiro recebe notificacao automatica, revisa pendencias em ate 24h e emite nota de credito se necessario. Somente finalize após o cliente validar o recibo digital enviado pelo CRM.
- **Excecoes aprovadas pela diretoria**  
  Forca maior (apagao, desastre, falha critica) permite reembolso de 100% mesmo dentro de 48h. Projetos com verba publica exigem aprovacao dupla (diretor comercial + juridico com termo). Cada excecao entra em ata mensal para auditoria.

### procedimentos_operacionais.pdf
- **Checklist de abertura do escritorio**  
  Chegar 30 minutos antes, ligar climatizacao em 22 graus, testar conectividade em todas as salas e confirmar a sincronizacao noturna do servidor local. Registrar alertas no dashboard Facility Ops e avisar o plantao via Teams.
- **Atendimento ao cliente hibrido**  
  Resposta inicial em ate 10 min por chat/telefone e follow-up completo em ate 2 horas. Usar script de qualificacao (contexto, objetivo, restricoes). Se envolver dados sensiveis, escale para o especialista de seguranca.
- **Protecao de dados compartilhados**  
  Digitalizar documentos impressos e enviar ao cofre S3 privado com tag confidencial; destruir no triturador nivel P4. Dados recebidos por e-mail precisam ser mascarados antes de subir ao banco vetorial. Nunca usar pen drives pessoais ou softwares nao homologados.
- **Plano de resposta a incidentes**  
  Em falha critica, acione Codigo Ambar no Slack e preencha o formulario IR-01. O lider de turno conduz a ponte, nomeia relator e registra decisoes minuto a minuto. Em ate 12h a equipe de melhoria continua publica resumo e agenda revisao com as partes.

## Observacoes
- O `PGVector` de `langchain_community` sera descontinuado; considere migrar futuramente para `langchain_postgres` com colunas JSONB para metadados.
- Sempre rode `python ingest.py` apos alterar PDFs ou adicionar novos documentos na pasta `data/`.
