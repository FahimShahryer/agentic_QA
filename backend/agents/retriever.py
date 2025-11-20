from config import TOP_K_RESULTS
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
import logging

logger = logging.getLogger(__name__)


class RetrieverAgent:
    """Agent responsible for retrieving relevant chunks using hybrid search."""

    def __init__(self, vectorstore, chunks: list = None, distance_threshold: float = None,
                 semantic_weight: float = 0.5):
        """
        Initialize RetrieverAgent with hybrid search.

        Args:
            vectorstore: FAISS vectorstore instance
            chunks: List of Document objects for BM25 (keyword search)
            distance_threshold: Max L2 distance to consider relevant (lower = stricter)
            semantic_weight: Weight for semantic search (0-1), keyword gets 1-semantic_weight
        """
        if vectorstore is None:
            raise ValueError("Vectorstore cannot be None")

        self.vectorstore = vectorstore
        self.distance_threshold = distance_threshold
        self.semantic_weight = semantic_weight
        self.chunks = chunks

        # Setup hybrid retriever if chunks provided
        self.hybrid_retriever = None
        if chunks:
            self._setup_hybrid_retriever(chunks)

    def _setup_hybrid_retriever(self, chunks: list):
        """Setup hybrid retriever combining BM25 and FAISS."""
        try:
            # BM25 for keyword search
            bm25_retriever = BM25Retriever.from_documents(chunks)
            bm25_retriever.k = TOP_K_RESULTS

            # FAISS for semantic search
            faiss_retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": TOP_K_RESULTS}
            )

            # Combine both
            self.hybrid_retriever = EnsembleRetriever(
                retrievers=[bm25_retriever, faiss_retriever],
                weights=[1 - self.semantic_weight, self.semantic_weight]
            )
            logger.info("Hybrid retriever initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to setup hybrid retriever: {e}. Using semantic only.")
            self.hybrid_retriever = None

    def retrieve(self, question: str, top_k: int = None, use_hybrid: bool = True) -> list:
        """
        Retrieve relevant chunks for a question.

        Args:
            question: User's question
            top_k: Number of chunks to retrieve (default from config)
            use_hybrid: Use hybrid search if available

        Returns:
            List of chunks with content, metadata, and scores
        """
        if not question or not question.strip():
            logger.warning("Empty question provided to retriever")
            return []

        k = top_k or TOP_K_RESULTS

        try:
            # Use hybrid retriever if available and requested
            if use_hybrid and self.hybrid_retriever:
                docs = self.hybrid_retriever.invoke(question)
                # Limit results
                docs = docs[:k]
                # Format without scores (hybrid doesn't return scores)
                chunks = []
                for doc in docs:
                    chunks.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'score': None  # Hybrid doesn't provide scores
                    })
            else:
                # Semantic search only with scores
                results = self.vectorstore.similarity_search_with_score(question, k=k)
                chunks = []
                for doc, score in results:
                    if self.distance_threshold and score > self.distance_threshold:
                        continue
                    chunks.append({
                        'content': doc.page_content,
                        'metadata': doc.metadata,
                        'score': round(score, 4)
                    })

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise RuntimeError(f"Failed to search documents: {str(e)}")

        logger.info(f"Retrieved {len(chunks)} chunks for question: {question[:50]}...")
        return chunks

    def retrieve_with_filter(self, question: str, source_filter: str = None, top_k: int = None) -> list:
        """
        Retrieve chunks with optional source filtering.

        Args:
            question: User's question
            source_filter: Only return chunks from this source file
            top_k: Number of chunks to retrieve

        Returns:
            Filtered list of chunks
        """
        chunks = self.retrieve(question, top_k)

        if source_filter:
            chunks = [
                c for c in chunks
                if c['metadata'].get('source', '').lower() == source_filter.lower()
            ]

        return chunks
