def split_text_into_chunks(
    *,
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    if not text:
        return []
    if chunk_size <= 0:
        return [text]

    chunks: list[str] = []
    start = 0
    min_break_index = int(chunk_size * _MIN_BREAK_RATIO)
    text_len = len(text)
    while start < text_len:
        end = min(text_len, start + chunk_size)
        if end < text_len:
            window = text[start:end]
            cut = _find_break_index(window, min_break_index)
            if cut is not None and cut > 0:
                end = start + cut

        if end <= start:
            end = min(text_len, start + chunk_size)

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break

        next_start = end - chunk_overlap
        if next_start <= start:
            next_start = end
        start = max(0, next_start)

    return chunks