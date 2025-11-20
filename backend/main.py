from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import logging
from session_manager import session_manager
from config import UPLOAD_DIR

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG Document QA API",
    description="Upload PDFs and ask questions with citations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


# Pydantic models
class QuestionRequest(BaseModel):
    session_id: str
    question: str


class SessionResponse(BaseModel):
    session_id: str
    message: str


# Routes

@app.get("/")
async def root():
    """Serve frontend or return API info."""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "RAG Document QA API", "docs": "/docs"}


@app.post("/api/session", response_model=SessionResponse)
async def create_session():
    """Create a new session."""
    try:
        session_id = session_manager.create_session()
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully"
        )
    except Exception as e:
        logger.error(f"Failed to create session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """Delete session and cleanup all data."""
    try:
        if not session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        session_manager.delete_session(session_id)
        return {"message": "Session deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information."""
    try:
        if not session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        return session_manager.get_session_info(session_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_documents(
    session_id: str = Form(...),
    files: list[UploadFile] = File(...)
):
    """Upload PDF documents to a session."""
    try:
        if not session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_manager.get_session(session_id)

        # Save uploaded files
        saved_paths = []
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Only PDF files are allowed: {file.filename}"
                )

            # Save file
            file_path = os.path.join(session.upload_dir, file.filename)
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            saved_paths.append(file_path)
            logger.info(f"Saved file: {file_path}")

        # Process documents
        result = session.add_documents(saved_paths)

        return {
            "message": "Documents uploaded and processed successfully",
            "documents": result['documents'],
            "total_chunks": result['total_chunks']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question about uploaded documents."""
    try:
        if not session_manager.session_exists(request.session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_manager.get_session(request.session_id)
        response = session.ask(request.question)

        return {
            "answer": response['answer'],
            "references": response['references'],
            "chunks_used": response['chunks_used'],
            "sources": response['sources']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process question: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/documents/{session_id}")
async def get_documents(session_id: str):
    """Get list of uploaded documents in a session."""
    try:
        if not session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_manager.get_session(session_id)
        return {"documents": session.documents}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history/{session_id}")
async def get_chat_history(session_id: str):
    """Get chat history for a session."""
    try:
        if not session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_manager.get_session(session_id)
        return {"history": session.get_chat_history()}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear chat history but keep documents."""
    try:
        if not session_manager.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_manager.get_session(session_id)
        session.clear_chat()
        return {"message": "Chat history cleared"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear chat history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
