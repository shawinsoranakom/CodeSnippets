def _split_text_by_pattern(text, pattern):
    # Split text by the compiled delimiter pattern and keep delimiter text in each chunk.
    if not pattern:
        return [text or ""]

    split_texts = re.split(r"(%s)" % pattern, text or "", flags=re.DOTALL)
    chunks = []
    for i in range(0, len(split_texts), 2):
        chunk = split_texts[i]
        if not chunk:
            continue
        if i + 1 < len(split_texts):
            chunk += split_texts[i + 1]
        if chunk.strip():
            chunks.append(chunk)
    return chunks