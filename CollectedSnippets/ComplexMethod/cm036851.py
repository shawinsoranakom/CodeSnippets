def _sse_delta_contents(sse_body: str) -> list[str]:
    """Extract ``choices[0].delta.content`` from each ``data:`` line (streaming API)."""
    contents: list[str] = []
    for line in sse_body.splitlines():
        if not line.startswith("data: "):
            continue
        payload = line.removeprefix("data: ").strip()
        if payload == "[DONE]":
            continue
        obj = json.loads(payload)
        for choice in obj.get("choices") or []:
            delta = choice.get("delta") or {}
            if "content" in delta:
                contents.append(delta["content"])
    return contents