def chunk_documents(
    documents: Iterable[str],
    chunk_token_threshold: int,
    overlap: int,
    word_token_rate: float = 0.75,
    tokenizer: Optional[Callable[[str], List[str]]] = None,
) -> Generator[str, None, None]:
    """
    Efficiently chunks documents into token-limited sections with overlap between chunks.

    Args:
        documents: Iterable of document strings
        chunk_token_threshold: Maximum tokens per chunk
        overlap: Number of tokens to overlap between chunks
        word_token_rate: Token estimate per word when not using a tokenizer
        tokenizer: Function that splits text into tokens (if available)

    Yields:
        Text chunks as strings
    """
    token_queue = deque()
    contribution_queue = deque()
    current_token_count = 0.0

    for doc in documents:
        # Tokenize document
        if tokenizer:
            tokens = tokenizer(doc)
            contributions = [1.0] * len(tokens)
        else:
            tokens = doc.split()
            contributions = [word_token_rate] * len(tokens)

        # Add to processing queues
        token_queue.extend(tokens)
        contribution_queue.extend(contributions)
        current_token_count += sum(contributions)

        # Process full chunks
        while current_token_count >= chunk_token_threshold:
            # Find chunk split point
            chunk_tokens = []
            chunk_contrib = []
            chunk_total = 0.0

            # Build chunk up to threshold
            while contribution_queue:
                next_contrib = contribution_queue[0]
                if chunk_total + next_contrib > chunk_token_threshold:
                    break

                chunk_total += next_contrib
                chunk_contrib.append(contribution_queue.popleft())
                chunk_tokens.append(token_queue.popleft())

            # Handle edge case where first token exceeds threshold
            if not chunk_contrib:  # Single token exceeds threshold
                chunk_contrib.append(contribution_queue.popleft())
                chunk_tokens.append(token_queue.popleft())

            # Calculate overlap
            overlap_total = 0.0
            overlap_idx = 0
            for contrib in reversed(chunk_contrib):
                if overlap_total + contrib > overlap:
                    break
                overlap_total += contrib
                overlap_idx += 1

            # Prepend overlap to queues
            if overlap_idx > 0:
                overlap_tokens = chunk_tokens[-overlap_idx:]
                overlap_contrib = chunk_contrib[-overlap_idx:]

                token_queue.extendleft(reversed(overlap_tokens))
                contribution_queue.extendleft(reversed(overlap_contrib))
                current_token_count += overlap_total

            # Update current token count and yield chunk
            current_token_count -= sum(chunk_contrib)
            yield " ".join(chunk_tokens[:len(chunk_tokens)-overlap_idx] if overlap_idx else chunk_tokens)

    # Yield remaining tokens
    if token_queue:
        yield " ".join(token_queue)