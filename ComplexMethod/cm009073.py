def _get_len_safe_embeddings(
        self,
        texts: list[str],
        *,
        engine: str,
        chunk_size: int | None = None,
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate length-safe embeddings for a list of texts.

        This method handles tokenization and embedding generation, respecting the
        `embedding_ctx_length` and `chunk_size`. Supports both `tiktoken` and
        HuggingFace `transformers` based on the `tiktoken_enabled` flag.

        Args:
            texts: The list of texts to embed.
            engine: The engine or model to use for embeddings.
            chunk_size: The size of chunks for processing embeddings.

        Returns:
            A list of embeddings for each input text.
        """
        _chunk_size = chunk_size or self.chunk_size
        client_kwargs = {**self._invocation_params, **kwargs}
        _iter, tokens, indices, token_counts = self._tokenize(texts, _chunk_size)
        batched_embeddings: list[list[float]] = []

        # Process in batches respecting the token limit
        i = 0
        while i < len(tokens):
            # Determine how many chunks we can include in this batch
            batch_token_count = 0
            batch_end = i

            for j in range(i, min(i + _chunk_size, len(tokens))):
                chunk_tokens = token_counts[j]
                # Check if adding this chunk would exceed the limit
                if batch_token_count + chunk_tokens > MAX_TOKENS_PER_REQUEST:
                    if batch_end == i:
                        # Single chunk exceeds limit - handle it anyway
                        batch_end = j + 1
                    break
                batch_token_count += chunk_tokens
                batch_end = j + 1

            # Make API call with this batch
            batch_tokens = tokens[i:batch_end]
            response = self.client.create(input=batch_tokens, **client_kwargs)
            if not isinstance(response, dict):
                response = response.model_dump()
            batched_embeddings.extend(r["embedding"] for r in response["data"])

            i = batch_end

        embeddings = _process_batched_chunked_embeddings(
            len(texts), tokens, batched_embeddings, indices, self.skip_empty
        )
        _cached_empty_embedding: list[float] | None = None

        def empty_embedding() -> list[float]:
            nonlocal _cached_empty_embedding
            if _cached_empty_embedding is None:
                average_embedded = self.client.create(input="", **client_kwargs)
                if not isinstance(average_embedded, dict):
                    average_embedded = average_embedded.model_dump()
                _cached_empty_embedding = average_embedded["data"][0]["embedding"]
            return _cached_empty_embedding

        return [e if e is not None else empty_embedding() for e in embeddings]