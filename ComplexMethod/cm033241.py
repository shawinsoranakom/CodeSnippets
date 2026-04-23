def _normalize_text_from_content(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for blk in content:
            if isinstance(blk, dict):
                if blk.get("type") in {"text", "input_text"}:
                    txt = blk.get("text")
                    if txt:
                        texts.append(str(txt))
                elif "text" in blk and isinstance(blk.get("text"), (str, int, float)):
                    texts.append(str(blk["text"]))
        return "\n".join(texts).strip()
    return str(content)