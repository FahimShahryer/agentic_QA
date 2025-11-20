import uuid
import os
import shutil
import logging
from datetime import datetime
from config import UPLOAD_DIR
from ingestion import DocumentIngestion
from chain import QAChain

logger = logging.getLogger(__name__)


class Session:
    """Represents a single user session."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.ingestion = DocumentIngestion()
        self.qa_chain = None
        self.documents = []  # List of uploaded document names
        self.upload_dir = os.path.join(UPLOAD_DIR, session_id)

        # Create session upload directory
        os.makedirs(self.upload_dir, exist_ok=True)
        logger.info(f"Session created: {session_id}")

    def add_documents(self, file_paths: list) -> dict:
        """
        Process and add documents to the session.

        Args:
            file_paths: List of PDF file paths

        Returns:
            Dict with status and document info
        """
        try:
            vectorstore, chunks = self.ingestion.process_pdfs(file_paths)

            # Create QA chain with hybrid search
            self.qa_chain = QAChain(vectorstore, chunks=chunks)

            # Track document names
            for path in file_paths:
                doc_name = os.path.basename(path)
                if doc_name not in self.documents:
                    self.documents.append(doc_name)

            logger.info(f"Session {self.session_id}: Added {len(file_paths)} documents")

            return {
                'status': 'success',
                'documents': self.documents,
                'total_chunks': len(chunks)
            }

        except Exception as e:
            logger.error(f"Session {self.session_id}: Failed to add documents - {str(e)}")
            raise

    def ask(self, question: str) -> dict:
        """
        Ask a question in this session.

        Args:
            question: User's question

        Returns:
            Response dict with answer and references
        """
        if self.qa_chain is None:
            return {
                'answer': "Please upload documents first.",
                'references': "",
                'chunks_used': 0,
                'sources': []
            }

        return self.qa_chain.ask(question)

    def get_chat_history(self) -> list:
        """Get chat history for this session."""
        if self.qa_chain is None:
            return []
        return self.qa_chain.get_chat_history()

    def clear_chat(self):
        """Clear chat history but keep documents."""
        if self.qa_chain:
            self.qa_chain.clear_memory()
            logger.info(f"Session {self.session_id}: Chat history cleared")

    def cleanup(self):
        """Clean up all session data."""
        # Clear ingestion data
        self.ingestion.clear()

        # Clear QA chain
        self.qa_chain = None
        self.documents = []

        # Delete uploaded files
        if os.path.exists(self.upload_dir):
            shutil.rmtree(self.upload_dir)
            logger.info(f"Session {self.session_id}: Deleted upload directory")

        logger.info(f"Session {self.session_id}: Cleanup complete")


class SessionManager:
    """Manages multiple user sessions."""

    def __init__(self):
        self.sessions = {}

    def create_session(self) -> str:
        """
        Create a new session.

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = Session(session_id)
        logger.info(f"SessionManager: Created session {session_id}")
        return session_id

    def get_session(self, session_id: str) -> Session:
        """
        Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session object

        Raises:
            KeyError: If session not found
        """
        if session_id not in self.sessions:
            raise KeyError(f"Session not found: {session_id}")
        return self.sessions[session_id]

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self.sessions

    def delete_session(self, session_id: str):
        """
        Delete a session and clean up all data.

        Args:
            session_id: Session ID to delete
        """
        if session_id in self.sessions:
            self.sessions[session_id].cleanup()
            del self.sessions[session_id]
            logger.info(f"SessionManager: Deleted session {session_id}")

    def get_all_sessions(self) -> list:
        """Get list of all active session IDs."""
        return list(self.sessions.keys())

    def get_session_info(self, session_id: str) -> dict:
        """
        Get information about a session.

        Args:
            session_id: Session ID

        Returns:
            Dict with session info
        """
        session = self.get_session(session_id)
        return {
            'session_id': session_id,
            'created_at': session.created_at.isoformat(),
            'documents': session.documents,
            'has_qa_chain': session.qa_chain is not None,
            'chat_history_length': len(session.get_chat_history())
        }

    def cleanup_all(self):
        """Clean up all sessions."""
        for session_id in list(self.sessions.keys()):
            self.delete_session(session_id)
        logger.info("SessionManager: All sessions cleaned up")


# Global session manager instance
session_manager = SessionManager()
