# Multi-Agent AI Customer Support Assistant using RAG and LLMs

This repository is a complete capstone implementation with:

- React customer chat interface
- FastAPI backend and REST APIs
- Register/login and JWT authentication
- Conversation/session history
- Intent Detection Agent
- Multi-Agent Router
- Billing Agent
- Technical Support Agent
- Product Agent
- Complaint Agent
- FAQ Agent
- Retrieval-Augmented Generation (RAG)
- `sentence-transformers/all-MiniLM-L6-v2`
- FAISS vector database
- OpenAI-compatible LLM integration
- Human escalation and ticket creation
- Analytics endpoint
- PostgreSQL-ready persistence
- Unit tests and routing evaluation
- 8 fictional-company knowledge base PDFs
- Project report and demonstration script

## Architecture

Customer -> React Chat -> FastAPI -> Auth + Conversation Memory -> Intent Detection -> Agent Router -> Specialized Agent(s) -> RAG -> FAISS -> Company PDFs -> LLM -> Response Aggregator -> Final Answer -> Optional Human Escalation

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Install:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and add an LLM key.

Groq example:

```env
LLM_API_KEY=YOUR_GROQ_KEY
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
```

Then:

```bash
uvicorn app.main:app --reload --port 8000
```

Open:

- API health: `http://localhost:8000/api/health`
- Swagger: `http://localhost:8000/docs`

On first use the system downloads the sentence-transformer model and creates the FAISS index from `knowledge_base/*.pdf`.

### 2. Frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

`http://localhost:5173`

Register a new account and start chatting.

## PostgreSQL mode

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Set in `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://support:support@localhost:5432/support_ai
```

Restart FastAPI.

## Demo queries

**Billing**
`I was charged twice for my subscription. What should I do?`

**Technical**
`My password reset link does not work and I cannot login.`

**Product**
`Compare Basic and Premium plans.`

**Complaint**
`I am frustrated because this issue is still unresolved. I want to escalate it.`

**FAQ**
`What are your support hours?`

**Multi-agent**
`I paid yesterday but Premium is still locked.`

Expected: Billing + Technical.

**RAG**
`How long does an approved refund take?`

Open **Retrieved sources** below the answer.

**Memory**
First: `Tell me about Premium.`
Then: `How much does it cost?`

## Testing

```bash
cd backend
pytest -q
python evaluate.py
```

The evaluation script reports intent-routing accuracy and latency.

## REST APIs

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/chat`
- `GET /api/conversations`
- `GET /api/conversations/{id}`
- `GET /api/analytics`
- `POST /api/rag/reindex`

## How RAG works

1. Read company PDFs with PyPDF.
2. Split text into overlapping chunks.
3. Generate MiniLM sentence embeddings.
4. Normalize and save vectors in FAISS.
5. Embed each incoming user query.
6. Retrieve the most relevant chunks.
7. Give retrieved context and recent conversation history to the selected agent(s).
8. Generate a grounded answer.
9. Display retrieved PDF sources to the user.

## Human escalation

The backend creates a support ticket when:
- retrieval confidence is low,
- an agent explicitly recommends human review, or
- a negative complaint appears unresolved.

## Submission checklist

Already included:
- source code
- project report PDF
- README
- knowledge-base PDFs
- sample dataset
- demo-video script

You still need to:
1. run the project,
2. record the demonstration video,
3. optionally deploy and add links if required by your evaluator.

## Deployment

Frontend: Vercel

Set:
`VITE_API_URL=https://YOUR-BACKEND/api`

Backend: Render or Railway

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Set environment variables:
`DATABASE_URL`, `JWT_SECRET`, `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `CORS_ORIGINS`.

## LLM key note

If no `LLM_API_KEY` is configured, the app falls back to an extractive RAG response so routing and retrieval can still be demonstrated. For the final submission, configure a valid OpenAI-compatible API key so LLM integration is visibly demonstrated.
