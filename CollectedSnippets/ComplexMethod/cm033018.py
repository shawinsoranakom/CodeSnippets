def _extract_rich_text(self, rich_text_array: list[dict[str, Any]]) -> str:
        collected_text: list[str] = []
        for rich_text in rich_text_array:
            content = ""
            r_type = rich_text.get("type")

            if r_type == "equation":
                expr = rich_text.get("equation", {}).get("expression")
                if expr:
                    content = expr
            elif r_type == "mention":
                mention = rich_text.get("mention", {}) or {}
                mention_type = mention.get("type")
                mention_value = mention.get(mention_type, {}) if mention_type else {}
                if mention_type == "date":
                    start = mention_value.get("start")
                    end = mention_value.get("end")
                    if start and end:
                        content = f"{start} - {end}"
                    elif start:
                        content = start
                elif mention_type in {"page", "database"}:
                    content = mention_value.get("id", rich_text.get("plain_text", ""))
                elif mention_type == "link_preview":
                    content = mention_value.get("url", rich_text.get("plain_text", ""))
                else:
                    content = rich_text.get("plain_text", "") or str(mention_value)
            else:
                if rich_text.get("plain_text"):
                    content = rich_text["plain_text"]
                elif "text" in rich_text and rich_text["text"].get("content"):
                    content = rich_text["text"]["content"]

            href = rich_text.get("href")
            if content and href:
                content = f"{content} ({href})"

            if content:
                collected_text.append(content)

        return "".join(collected_text).strip()