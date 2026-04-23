def _chunk_transcript(self, transcript_data):
        """Group transcript segments into time-based chunks."""
        chunks = []
        current_chunk = []
        chunk_start = 0

        for segment in transcript_data:
            # Handle both dict (old API) and object (new API) formats
            segment_start = segment.start if hasattr(segment, "start") else segment["start"]

            # If this segment starts beyond the current chunk window, start a new chunk
            if segment_start - chunk_start >= self.chunk_size_seconds and current_chunk:
                chunk_text = " ".join(s.text if hasattr(s, "text") else s["text"] for s in current_chunk)
                chunks.append({"start": chunk_start, "text": chunk_text})
                current_chunk = []
                chunk_start = segment_start

            current_chunk.append(segment)

        # Add the last chunk
        if current_chunk:
            chunk_text = " ".join(s.text if hasattr(s, "text") else s["text"] for s in current_chunk)
            chunks.append({"start": chunk_start, "text": chunk_text})

        return chunks