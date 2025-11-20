from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from config import OPENAI_API_KEY, CHUNK_SIZE, CHUNK_OVERLAP, UPLOAD_DIR
import os
import logging

logger = logging.getLogger(__name__)


class DocumentIngestion:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vectorstore = None
        self.chunks = []  # Store chunks for hybrid search

    def load_pdf(self, file_path: str) -> list:
        """Load a single PDF and return documents with metadata."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        except Exception as e:
            logger.error(f"Failed to load PDF {file_path}: {str(e)}")
            raise RuntimeError(f"Failed to load PDF: {str(e)}")

        # Add source filename to metadata
        filename = os.path.basename(file_path)
        for doc in documents:
            doc.metadata['source'] = filename

        logger.info(f"Loaded {len(documents)} pages from {filename}")
        return documents

    def load_multiple_pdfs(self, file_paths: list) -> list:
        """Load multiple PDFs and combine documents."""
        if not file_paths:
            raise ValueError("No file paths provided")

        all_documents = []
        for file_path in file_paths:
            try:
                documents = self.load_pdf(file_path)
                all_documents.extend(documents)
            except Exception as e:
                logger.warning(f"Skipping {file_path}: {str(e)}")
                continue

        if not all_documents:
            raise RuntimeError("No documents were successfully loaded")

        logger.info(f"Total documents loaded: {len(all_documents)}")
        return all_documents

    def chunk_documents(self, documents: list) -> list:
        """Split documents into chunks with metadata."""
        chunks = self.text_splitter.split_documents(documents)

        # Add chunk_id to metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_id'] = f"{chunk.metadata['source']}_chunk_{i}"

        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    def create_vectorstore(self, chunks: list) -> FAISS:
        """Create FAISS vectorstore from chunks."""
        try:
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
            logger.info("FAISS vectorstore created successfully")
        except Exception as e:
            logger.error(f"Failed to create vectorstore: {str(e)}")
            raise RuntimeError(f"Failed to create vectorstore: {str(e)}")

        return self.vectorstore

    def add_to_vectorstore(self, chunks: list) -> FAISS:
        """Add new chunks to existing vectorstore."""
        if self.vectorstore is None:
            return self.create_vectorstore(chunks)

        try:
            self.vectorstore.add_documents(chunks)
            logger.info(f"Added {len(chunks)} chunks to existing vectorstore")
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise RuntimeError(f"Failed to add documents: {str(e)}")

        return self.vectorstore

    def process_pdfs(self, file_paths: list) -> tuple:
        """
        Complete pipeline: load PDFs → chunk → create vectorstore.

        Returns:
            Tuple of (vectorstore, chunks) for use with RetrieverAgent
        """
        # Load all PDFs
        documents = self.load_multiple_pdfs(file_paths)

        # Chunk documents
        new_chunks = self.chunk_documents(documents)

        # Store chunks for hybrid search
        self.chunks.extend(new_chunks)

        # Create or update vectorstore
        if self.vectorstore is None:
            self.create_vectorstore(new_chunks)
        else:
            self.add_to_vectorstore(new_chunks)

        return self.vectorstore, self.chunks

    def get_chunks(self) -> list:
        """Get all stored chunks."""
        return self.chunks

    def clear(self):
        """Clear vectorstore and chunks."""
        self.vectorstore = None
        self.chunks = []
        logger.info("Cleared vectorstore and chunks")
