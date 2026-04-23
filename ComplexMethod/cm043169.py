def merge_chunks(
    docs: Sequence[str], 
    target_size: int,
    overlap: int = 0,
    word_token_ratio: float = 1.0,
    splitter: Callable = None
) -> List[str]:
    """
    Merges a sequence of documents into chunks based on a target token count, with optional overlap.

    Each document is split into tokens using the provided splitter function (defaults to str.split). Tokens are distributed into chunks aiming for the specified target size, with optional overlapping tokens between consecutive chunks. Returns a list of non-empty merged chunks as strings.

    Args:
        docs: Sequence of input document strings to be merged.
        target_size: Target number of tokens per chunk.
        overlap: Number of tokens to overlap between consecutive chunks.
        word_token_ratio: Multiplier to estimate token count from word count.
        splitter: Callable used to split each document into tokens.

    Returns:
        List of merged document chunks as strings, each not exceeding the target token size.
    """
    # Pre-tokenize all docs and store token counts
    splitter = splitter or str.split
    token_counts = array('I')
    all_tokens: List[List[str]] = []
    total_tokens = 0

    for doc in docs:
        tokens = splitter(doc)
        count = int(len(tokens) * word_token_ratio)
        if count:  # Skip empty docs
            token_counts.append(count)
            all_tokens.append(tokens)
            total_tokens += count

    if not total_tokens:
        return []

    # Pre-allocate chunks
    num_chunks = max(1, (total_tokens + target_size - 1) // target_size)
    chunks: List[List[str]] = [[] for _ in range(num_chunks)]

    curr_chunk = 0
    curr_size = 0

    # Distribute tokens
    for tokens in chain.from_iterable(all_tokens):
        if curr_size >= target_size and curr_chunk < num_chunks - 1:
            if overlap > 0:
                overlap_tokens = chunks[curr_chunk][-overlap:]
                curr_chunk += 1
                chunks[curr_chunk].extend(overlap_tokens)
                curr_size = len(overlap_tokens)
            else:
                curr_chunk += 1
                curr_size = 0

        chunks[curr_chunk].append(tokens)
        curr_size += 1

    # Return only non-empty chunks
    return [' '.join(chunk) for chunk in chunks if chunk]