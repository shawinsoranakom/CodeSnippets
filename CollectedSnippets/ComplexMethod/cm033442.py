def chunk_content(self, document: RAGFlowDocument, 
                     chunk_size: int = 1000, 
                     chunk_overlap: int = 200) -> List[Dict[str, Any]]:
        """Chunk document content for RAG processing."""
        content = document.content
        chunks = []

        if len(content) <= chunk_size:
            return [{
                "id": f"{document.id}_chunk_0",
                "content": content,
                "metadata": {
                    **document.metadata,
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            }]

        # Split content into chunks
        start = 0
        chunk_index = 0

        while start < len(content):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence endings
                sentence_end = content.rfind('.', start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1

            chunk_content = content[start:end].strip()

            if chunk_content:
                chunks.append({
                    "id": f"{document.id}_chunk_{chunk_index}",
                    "content": chunk_content,
                    "metadata": {
                        **document.metadata,
                        "chunk_index": chunk_index,
                        "total_chunks": len(chunks) + 1,  # Will be updated
                        "chunk_start": start,
                        "chunk_end": end
                    }
                })
                chunk_index += 1

            # Move start position with overlap
            start = end - chunk_overlap
            if start >= len(content):
                break

        # Update total chunks count
        for chunk in chunks:
            chunk["metadata"]["total_chunks"] = len(chunks)

        return chunks