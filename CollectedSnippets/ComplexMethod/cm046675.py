def anthropic_messages_to_openai(
    messages: list[dict],
    system: Optional[Union[str, list]] = None,
) -> list[dict]:
    """Convert Anthropic messages + system to OpenAI-format message dicts.

    User messages that carry ``image`` blocks are emitted as OpenAI
    multimodal content arrays (``[{type: "text", ...}, {type: "image_url", ...}]``)
    so they flow through llama-server's native vision pathway.
    """
    result: list[dict] = []

    # System prompt
    if system:
        if isinstance(system, str):
            result.append({"role": "system", "content": system})
        elif isinstance(system, list):
            parts = []
            for block in system:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block["text"])
                elif isinstance(block, str):
                    parts.append(block)
            if parts:
                result.append({"role": "system", "content": "\n".join(parts)})

    for msg in messages:
        role = msg["role"] if isinstance(msg, dict) else msg.role
        content = msg["content"] if isinstance(msg, dict) else msg.content

        if isinstance(content, str):
            result.append({"role": role, "content": content})
            continue

        if role == "assistant":
            # Assistant content carries text + tool_use; images aren't
            # part of Anthropic's assistant content model.
            text_parts: list[str] = []
            tool_calls: list[dict] = []
            for block in content:
                b = block if isinstance(block, dict) else block.model_dump()
                btype = b.get("type", "")
                if btype == "text":
                    text_parts.append(b["text"])
                elif btype == "tool_use":
                    tool_calls.append(
                        {
                            "id": b["id"],
                            "type": "function",
                            "function": {
                                "name": b["name"],
                                "arguments": json.dumps(b["input"]),
                            },
                        }
                    )
            msg_dict: dict[str, Any] = {"role": "assistant"}
            if text_parts:
                msg_dict["content"] = "\n".join(text_parts)
            if tool_calls:
                msg_dict["tool_calls"] = tool_calls
            result.append(msg_dict)
            continue

        if role == "user":
            # Build an ordered part list so text/image interleaving is
            # preserved (e.g. [text, image, text, image]). tool_result
            # blocks become their own OpenAI "tool" role messages.
            user_parts: list[dict] = []
            has_image = False
            tool_results: list[dict] = []
            for block in content:
                b = block if isinstance(block, dict) else block.model_dump()
                btype = b.get("type", "")
                if btype == "text":
                    user_parts.append({"type": "text", "text": b["text"]})
                elif btype == "image":
                    part = _anthropic_image_block_to_openai_part(b)
                    if part is not None:
                        user_parts.append(part)
                        has_image = True
                elif btype == "tool_result":
                    tc = b.get("content", "")
                    if isinstance(tc, list):
                        tc = " ".join(
                            p["text"]
                            for p in tc
                            if isinstance(p, dict) and p.get("type") == "text"
                        )
                    tool_results.append(
                        {
                            "role": "tool",
                            "tool_call_id": b["tool_use_id"],
                            "content": str(tc),
                        }
                    )

            if has_image:
                result.append({"role": "user", "content": user_parts})
            else:
                # No images — collapse text parts to a plain string so
                # existing text-only callers keep their simple shape.
                text = "\n".join(p["text"] for p in user_parts)
                if text:
                    result.append({"role": "user", "content": text})
            for tr in tool_results:
                result.append(tr)

    return result