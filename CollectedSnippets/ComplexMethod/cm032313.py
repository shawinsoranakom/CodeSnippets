def get_highlight_from_messages(
    messages: list[dict] | None,
    keywords: list[str],
    field_name: str,
    is_english_fn: Callable[[str], bool] | None = None,
) -> dict[str, str]:
    """Build id -> highlighted text from a list of message dicts."""
    if not messages or not keywords:
        return {}

    ans = {}
    for doc in messages:
        doc_id = doc.get("id")
        if not doc_id:
            continue
        txt = doc.get(field_name)
        if not txt or not isinstance(txt, str):
            continue
        highlighted = highlight_text(txt, keywords, is_english_fn)
        if highlighted and re.search(r"<em>[^<>]+</em>", highlighted, flags=re.IGNORECASE | re.MULTILINE):
            ans[doc_id] = highlighted
    return ans