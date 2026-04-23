def _explode_reasoning(block: dict[str, Any]) -> Iterator[types.ReasoningContentBlock]:
    if "summary" not in block:
        yield cast("types.ReasoningContentBlock", block)
        return

    known_fields = {"type", "reasoning", "id", "index"}
    unknown_fields = [
        field for field in block if field != "summary" and field not in known_fields
    ]
    if unknown_fields:
        block["extras"] = {}
    for field in unknown_fields:
        block["extras"][field] = block.pop(field)

    if not block["summary"]:
        # [{'id': 'rs_...', 'summary': [], 'type': 'reasoning', 'index': 0}]
        block = {k: v for k, v in block.items() if k != "summary"}
        if "index" in block:
            meaningful_idx = f"{block['index']}_0"
            block["index"] = f"lc_rs_{meaningful_idx.encode().hex()}"
        yield cast("types.ReasoningContentBlock", block)
        return

    # Common part for every exploded line, except 'summary'
    common = {k: v for k, v in block.items() if k in known_fields}

    # Optional keys that must appear only in the first exploded item
    first_only = block.pop("extras", None)

    for idx, part in enumerate(block["summary"]):
        new_block = dict(common)
        new_block["reasoning"] = part.get("text", "")
        if idx == 0 and first_only:
            new_block.update(first_only)
        if "index" in new_block:
            summary_index = part.get("index", 0)
            meaningful_idx = f"{new_block['index']}_{summary_index}"
            new_block["index"] = f"lc_rs_{meaningful_idx.encode().hex()}"

        yield cast("types.ReasoningContentBlock", new_block)