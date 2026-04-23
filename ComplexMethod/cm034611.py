async def sse_stream(iter_lines: AsyncIterator[bytes]) -> AsyncIterator[dict]:
    if hasattr(iter_lines, "content"):
        iter_lines = iter_lines.content
    elif hasattr(iter_lines, "iter_lines"):
        iter_lines = iter_lines.iter_lines()
    async for line in iter_lines:
        if line.startswith(b"data:"):
            rest = line[5:].strip()
            if not rest:
                continue
            if rest.startswith(b"[DONE]"):
                break
            try:
                yield json.loads(rest)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON data: {rest}")