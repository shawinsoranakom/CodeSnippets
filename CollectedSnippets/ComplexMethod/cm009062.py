def _clean_block(block: dict) -> dict:
    # Remove "index" key added for message aggregation in langchain-core
    new_block = {k: v for k, v in block.items() if k != "index"}
    if block.get("type") == "thinking" and isinstance(block.get("thinking"), list):
        new_block["thinking"] = [
            (
                {k: v for k, v in sb.items() if k != "index"}
                if isinstance(sb, dict) and "index" in sb
                else sb
            )
            for sb in block["thinking"]
        ]
    return new_block