from agents.retriever import RetrieverAgent
from agents.qa_agent import QAAgent
from agents.formatter import FormatterAgent
import logging

logger = logging.getLogger(__name__)


class QAChain:
    """Orchestrator that coordinates all agents."""

    def __init__(self, vectorstore, chunks: list = None):
        """
        Initialize QAChain with all agents.

        Args:
            vectorstore: FAISS vectorstore
            chunks: Document chunks for hybrid search (optional)
        """
        self.retriever = RetrieverAgent(vectorstore, chunks=chunks)
        self.qa_agent = QAAgent()
        self.formatter = FormatterAgent()
        self.chat_history = []

    def ask(self, question: str) -> dict:
        """
        Process a question through all agents.

        Flow: Retriever → QA Agent → Formatter

        Args:
            question: User's question

        Returns:
            Formatted response with answer, references, metadata
        """
        if not question or not question.strip():
            return {
                'answer': "Please provide a valid question.",
                'references': "",
                'chunks_used': 0,
                'sources': []
            }

        try:
            # Step 1: Retrieve relevant chunks
            logger.info(f"Processing question: {question[:50]}...")
            chunks = self.retriever.retrieve(question)

            if not chunks:
                return {
                    'answer': "I couldn't find relevant information in the uploaded documents.",
                    'references': "",
                    'chunks_used': 0,
                    'sources': []
                }

            # Step 2: Generate answer with citations
            answer = self.qa_agent.generate(question, chunks, self.chat_history)

            # Step 3: Update chat history
            self.chat_history.append({"role": "user", "content": question})
            self.chat_history.append({"role": "assistant", "content": answer})

            # Step 4: Format final response
            response = self.formatter.format(answer, chunks)

            logger.info(f"Successfully processed question with {len(chunks)} chunks")
            return response

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            return {
                'answer': f"An error occurred while processing your question: {str(e)}",
                'references': "",
                'chunks_used': 0,
                'sources': []
            }

    def clear_memory(self):
        """Clear conversation history."""
        self.chat_history = []
        logger.info("Chat history cleared")

    def get_chat_history(self) -> list:
        """Get current chat history."""
        return self.chat_history
