from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from config import OPENAI_API_KEY, MODEL_NAME
import logging

logger = logging.getLogger(__name__)


class QAAgent:
    """Agent responsible for generating answers with citations using LCEL."""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=MODEL_NAME,
            temperature=0
        )
        self.chain = self._create_chain()

    def _create_chain(self):
        """Create LCEL chain for QA with citations."""
        prompt = ChatPromptTemplate.from_template("""
You are a helpful assistant answering questions based on document content.

Previous conversation:
{history}

Relevant context from documents:
{context}

INSTRUCTIONS:
- Answer based ONLY on the provided context
- Use inline citations like [1], [2] referring to chunk numbers above
- Be specific and detailed in your answers
- If the information is not in the context, say "I cannot find this information in the provided documents"

User question: {question}
""")

        chain = prompt | self.llm | StrOutputParser()
        return chain

    def format_history(self, history: list) -> str:
        """Format chat history as string."""
        if not history:
            return "No previous conversation."
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])

    def format_chunks(self, chunks: list) -> str:
        """Format retrieved chunks with numbers for citation."""
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            source = chunk['metadata'].get('source', 'Unknown')
            page = chunk['metadata'].get('page', None)
            content = chunk['content']

            # Handle page number safely
            if isinstance(page, int):
                page_str = str(page + 1)
            else:
                page_str = 'N/A'

            formatted.append(f"[{i}] (Source: {source}, Page {page_str}):\n{content}")
        return "\n\n".join(formatted)

    def generate(self, question: str, chunks: list, history: list) -> str:
        """
        Generate answer with citations.

        Args:
            question: User's question
            chunks: Retrieved chunks from RetrieverAgent
            history: Chat history

        Returns:
            Answer string with inline citations
        """
        if not chunks:
            return "No context available to answer the question."

        try:
            context = self.format_chunks(chunks)
            formatted_history = self.format_history(history)

            answer = self.chain.invoke({
                "question": question,
                "context": context,
                "history": formatted_history
            })

            logger.info(f"Generated answer for question: {question[:50]}...")
            return answer

        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            raise RuntimeError(f"Failed to generate answer: {str(e)}")
