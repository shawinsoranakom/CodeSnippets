def _strip_llm_fields(result: dict[str, Any]) -> dict[str, Any]:
    """Strip fields in *_STRIP_FROM_LLM* from every JSON text block in *result*.

    Called by *_truncating* AFTER the output has been stashed for the frontend
    SSE stream, so StreamToolOutputAvailable still receives the full payload
    (including ``is_dry_run``).  The returned dict is what the LLM sees.

    Non-JSON blocks, non-dict JSON values, and error results are returned unchanged.

    Note: only top-level keys are stripped. Nested occurrences of _STRIP_FROM_LLM
    fields (e.g. inside an ``outputs`` sub-dict) are not removed. Current tool
    responses only set these fields at the top level.
    """
    if result.get("isError"):
        return result
    content = result.get("content", [])
    new_content = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            raw = block.get("text", "")
            # Skip JSON parse/re-serialise round-trip when no stripped field
            # appears in the raw text — fast path for the common non-dry-run case.
            if not any(field in raw for field in _STRIP_FROM_LLM):
                new_content.append(block)
                continue
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                logger.debug("_strip_llm_fields: skipping non-JSON block: %s", exc)
                new_content.append(block)
                continue
            if isinstance(parsed, dict):
                for field in _STRIP_FROM_LLM:
                    parsed.pop(field, None)
                block = {**block, "text": json.dumps(parsed)}
        new_content.append(block)
    return {**result, "content": new_content}