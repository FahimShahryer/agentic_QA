# RAG Document QA

Upload PDFs and ask questions with citations using LangChain, FAISS, and OpenAI.

---
You can test it here LIVE! : https://agentic-qa.onrender.com/
---

## Features

- **Multi-PDF Upload** - Upload multiple PDFs per session
- **Hybrid Search** - BM25 keyword + FAISS semantic search
- **Chat Memory** - Context-aware follow-up questions
- **Citations** - Inline [1], [2] with page numbers
- **Session Management** - Isolated user sessions with full cleanup

---

## System Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Upload PDF │ →   │   Chunk +   │ →   │   FAISS +   │
│             │     │   Metadata  │     │    BM25     │
└─────────────┘     └─────────────┘     └─────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Question  │ →   │   Hybrid    │ →   │   LLM +     │
│             │     │   Retrieval │     │   Citations │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## Architecture

### Agents

| Agent | Role | Technology |
|-------|------|------------|
| RetrieverAgent | Find relevant chunks | FAISS + BM25 Ensemble |
| QAAgent | Generate answers | LCEL Chain + OpenAI |
| FormatterAgent | Format output + citations | Python |

### Pipeline

```
User Question → RetrieverAgent → QAAgent → FormatterAgent → Response
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | OpenAI API key |
| `MODEL_NAME` | gpt-4o-mini | LLM model |
| `CHUNK_SIZE` | 1000 | Characters per chunk |
| `CHUNK_OVERLAP` | 200 | Overlap between chunks |
| `TOP_K_RESULTS` | 5 | Chunks retrieved per query |

---

## Session Lifecycle

| Action | Documents | Memory | Vector Store |
|--------|-----------|--------|--------------|
| Upload | ✅ Added | - | ✅ Created |
| Ask | ✅ Kept | ✅ Updated | ✅ Searched |
| Clear Chat | ✅ Kept | ❌ Cleared | ✅ Kept |
| End Session | ❌ Deleted | ❌ Deleted | ❌ Deleted |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI Embeddings |
| Vector DB | FAISS |
| Framework | LangChain (LCEL) |
| Backend | FastAPI + Uvicorn |
| Frontend | HTML/CSS/JavaScript |
| Search | Hybrid (BM25 + Semantic) |

---

## Setup

### Local Development

1. Clone the repository
```bash
git clone https://github.com/FahimShahryer/agentic_QA.git
```

2. Create virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create `.env` file
```env
OPENAI_API_KEY=your-api-key-here
```

5. Run the server
```bash
cd backend
python main.py
```

6. Open http://localhost:8000

## Deployment on Render

### Steps

1. Push code to GitHub

2. Create new Web Service on Render
   - Connect your GitHub repo
   - Select Python environment

3. Configure Build & Start Commands:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

4. Add Environment Variables:
   - `OPENAI_API_KEY`: Your OpenAI API key

5. Deploy!

## Project Structure

```
qa_agents/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── ingestion.py         # PDF processing
│   ├── chain.py             # QA orchestrator
│   ├── session_manager.py   # Session handling
│   └── agents/
│       ├── retriever.py     # Hybrid search
│       ├── qa_agent.py      # Answer generation
│       └── formatter.py     # Output formatting
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── requirements.txt
└── .env
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/session` | Create session |
| DELETE | `/api/session/{id}` | Delete session |
| POST | `/api/upload` | Upload PDFs |
| POST | `/api/ask` | Ask question |
| GET | `/api/documents/{id}` | List documents |
| GET | `/api/history/{id}` | Get chat history |

## License

OPEN SOURCE!!