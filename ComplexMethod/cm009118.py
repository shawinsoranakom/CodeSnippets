def _implode_reasoning_blocks(blocks: list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    i = 0
    n = len(blocks)

    while i < n:
        block = blocks[i]

        # Skip non-reasoning blocks or blocks already in Responses format
        if block.get("type") != "reasoning" or "summary" in block:
            yield dict(block)
            i += 1
            continue
        elif "reasoning" not in block and "summary" not in block:
            # {"type": "reasoning", "id": "rs_..."}
            oai_format = {**block, "summary": []}
            if "extras" in oai_format:
                oai_format.update(oai_format.pop("extras"))
            oai_format["type"] = oai_format.pop("type", "reasoning")
            if "encrypted_content" in oai_format:
                oai_format["encrypted_content"] = oai_format.pop("encrypted_content")
            yield oai_format
            i += 1
            continue
        else:
            pass

        summary: list[dict[str, str]] = [
            {"type": "summary_text", "text": block.get("reasoning", "")}
        ]
        # 'common' is every field except the exploded 'reasoning'
        common = {k: v for k, v in block.items() if k != "reasoning"}
        if "extras" in common:
            common.update(common.pop("extras"))

        i += 1
        while i < n:
            next_ = blocks[i]
            if next_.get("type") == "reasoning" and "reasoning" in next_:
                summary.append(
                    {"type": "summary_text", "text": next_.get("reasoning", "")}
                )
                i += 1
            else:
                break

        merged = dict(common)
        merged["summary"] = summary
        merged["type"] = merged.pop("type", "reasoning")
        yield merged