import logging

logger = logging.getLogger(__name__)


class FormatterAgent:
    """Agent responsible for formatting final output with references."""

    def format(self, answer: str, chunks: list) -> dict:
        """
        Format the final response with answer and references.

        Args:
            answer: Generated answer from QAAgent
            chunks: Retrieved chunks with metadata

        Returns:
            Dictionary with answer, references, and metadata
        """
        references = self._build_references(chunks)

        return {
            'answer': answer,
            'references': references,
            'chunks_used': len(chunks),
            'sources': self._get_unique_sources(chunks)
        }

    def _build_references(self, chunks: list) -> str:
        """Build formatted reference list."""
        if not chunks:
            return ""

        references = "\n\n---\n**References:**\n"
        seen = set()
        citation_num = 1  # Track citation number separately

        for chunk in chunks:
            source = chunk['metadata'].get('source', 'Unknown')
            page = chunk['metadata'].get('page', None)
            key = f"{source}_{page}"

            if key not in seen:
                # Handle page number safely
                if isinstance(page, int):
                    page_str = str(page + 1)
                else:
                    page_str = 'N/A'

                references += f"[{citation_num}] {source}, Page {page_str}\n"
                seen.add(key)
                citation_num += 1

        return references

    def _get_unique_sources(self, chunks: list) -> list:
        """Get list of unique source documents used."""
        sources = set()
        for chunk in chunks:
            source = chunk['metadata'].get('source', 'Unknown')
            sources.add(source)
        return list(sources)
