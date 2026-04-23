def remove_toc_word(items, outlines):
    if not outlines:
        filtered_items, _ = remove_toc(items)
        return filtered_items
    outline_titles = [title.split("@@")[0].strip().lower() for title, _, _ in outlines if title]
    if outline_titles:
        indexed = [(_item_text(item), i) for i, item in enumerate(items)]
        i = 0
        while i < len(indexed):
            if not re.match(r"(contents|目录|目次|table of contents|致谢|acknowledge)$", indexed[i][0].split("@@")[0].strip().lower()):
                i += 1
                continue
            indexed.pop(i)
            while i < len(indexed):
                text = indexed[i][0]
                normalized = text.split("@@")[0].strip().lower()
                if not normalized:
                    indexed.pop(i)
                    continue
                if any(normalized.startswith(title) or title.startswith(normalized) for title in outline_titles):
                    indexed.pop(i)
                    continue
                if re.search(r"(\.{2,}|…{2,}|·{2,}|[ ]{2,})\s*\d+\s*$", text):
                    indexed.pop(i)
                    continue
                break
            break
        items = [items[i] for _, i in indexed]
    filtered_items, _ = remove_toc(items)
    return filtered_items