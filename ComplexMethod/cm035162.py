def _merge_runs(items) -> list:
    """Merge adjacent items with identical (bold, italic, underline, strikethrough, superscript, subscript, url).

    Returns [(bold, italic, underline, strikethrough, superscript, subscript, text, url)].
    """
    merged: list[tuple[bool, bool, bool, bool, bool, bool, str, str]] = []
    for (
        bold,
        italic,
        underline,
        strikethrough,
        superscript,
        subscript,
        text,
        url,
    ) in items:
        if not text:
            continue
        if (
            merged
            and merged[-1][0] == bold
            and merged[-1][1] == italic
            and merged[-1][2] == underline
            and merged[-1][3] == strikethrough
            and merged[-1][4] == superscript
            and merged[-1][5] == subscript
            and merged[-1][7] == url
        ):
            merged[-1] = (
                bold,
                italic,
                underline,
                strikethrough,
                superscript,
                subscript,
                merged[-1][6] + text,
                url,
            )
        else:
            merged.append(
                (
                    bold,
                    italic,
                    underline,
                    strikethrough,
                    superscript,
                    subscript,
                    text,
                    url,
                )
            )
    return merged