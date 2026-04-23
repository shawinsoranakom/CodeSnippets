def _json_split(
        self,
        data: Any,  # noqa: ANN401
        current_path: list[str] | None = None,
        chunks: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Split json into maximum size dictionaries while preserving structure."""
        current_path = current_path or []
        chunks = chunks if chunks is not None else [{}]
        if isinstance(data, dict) and data:
            for key, value in data.items():
                new_path = [*current_path, key]
                chunk_size = self._json_size(chunks[-1])
                size = self._json_size({key: value})
                remaining = self.max_chunk_size - chunk_size

                if size < remaining:
                    # Add item to current chunk
                    self._set_nested_dict(chunks[-1], new_path, value)
                else:
                    if chunk_size >= self.min_chunk_size:
                        # Chunk is big enough, start a new chunk
                        chunks.append({})

                    # Iterate
                    self._json_split(value, new_path, chunks)
        # Handle leaf values and empty dicts
        elif current_path:
            self._set_nested_dict(chunks[-1], current_path, data)
        return chunks