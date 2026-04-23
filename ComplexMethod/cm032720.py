def _extract_text_from_content(content):
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            texts = []
            for blk in content:
                if not isinstance(blk, dict):
                    continue
                if blk.get("type") in {"text", "input_text"} and blk.get("text"):
                    texts.append(str(blk["text"]))
                elif "text" in blk and isinstance(blk.get("text"), (str, int, float)):
                    texts.append(str(blk["text"]))
            return "\n".join(texts).strip()
        return ""