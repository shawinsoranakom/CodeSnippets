def _parse_messages_from_transcript(content: str) -> list[dict]:
    """Extract user/assistant messages from JSONL transcript for DB seeding."""
    messages: list[dict] = []
    for line in content.strip().split("\n"):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        msg = entry.get("message", {})
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue

        content_blocks = msg.get("content", "")
        if isinstance(content_blocks, list):
            # Flatten content blocks to text
            text_parts = []
            for block in content_blocks:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            text = "\n".join(text_parts)
        elif isinstance(content_blocks, str):
            text = content_blocks
        else:
            text = ""

        if text:
            messages.append({"role": role, "content": text})

    return messages