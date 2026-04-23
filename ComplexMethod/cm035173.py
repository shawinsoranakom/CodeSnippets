def _collect_from_parts(parts, seen: set) -> list:
        results = []
        for part in parts:
            try:
                if part.is_linked_to_previous:
                    continue
                texts = []
                for para in part.paragraphs:
                    try:
                        items = list(_iter_paragraph_items(para))
                        inline = _runs_to_markdown(items)
                        if not inline:
                            inline = para.text.strip()
                        if inline:
                            texts.append(inline)
                    except Exception:
                        pass
                text = " ".join(texts)
                # Filter: skip empty text, pure digits (page numbers),
                # page-number patterns (e.g. "第  页", "第6页", "共 页"), and duplicates
                if (
                    text
                    and not text.strip().isdigit()
                    and not _RE_PAGE_ONLY.match(text.strip())
                    and text not in seen
                ):
                    seen.add(text)
                    results.append(text)
            except Exception:
                pass
        return results