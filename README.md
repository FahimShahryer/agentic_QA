# RAG Document QA

Upload PDFs and ask questions with citations using LangChain, FAISS, and OpenAI.

## Features

- Multi-PDF upload
- Hybrid search (semantic + keyword)
- Chat with memory
- Citations with page numbers
- Session management

## Setup

### Local Development

1. Clone the repository
```bash
git clone <your-repo-url>
cd qa_agents
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
   - `PYTHON_VERSION`: 3.11

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

MIT
