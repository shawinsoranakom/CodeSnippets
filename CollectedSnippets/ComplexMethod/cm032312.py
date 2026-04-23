def highlight_text(
    txt: str,
    keywords: list[str],
    is_english_fn: Callable[[str], bool] | None = None,
) -> str:
    """Wrap keyword matches in text with <em>, by sentence.

    - If is_english_fn(sentence) is True: use word-boundary regex.
    - Otherwise: literal replace (longest keywords first).
    Only sentences that contain a match are included.
    """
    if not txt or not keywords:
        return ""

    txt = re.sub(r"[\r\n]", " ", txt, flags=re.IGNORECASE | re.MULTILINE)
    txt_list = []

    for t in re.split(r"[.?!;\n]", txt):
        t = t.strip()
        if not t:
            continue

        if is_english_fn is None or is_english_fn(t):
            for w in keywords:
                t = re.sub(
                    r"(^|[ .?/'\"\(\)!,:;-])(%s)([ .?/'\"\(\)!,:;-]|$)" % re.escape(w),
                    r"\1<em>\2</em>\3",
                    t,
                    flags=re.IGNORECASE | re.MULTILINE,
                )
        else:
            for w in sorted(keywords, key=len, reverse=True):
                t = re.sub(
                    re.escape(w),
                    f"<em>{w}</em>",
                    t,
                    flags=re.IGNORECASE | re.MULTILINE,
                )

        if re.search(r"<em>[^<>]+</em>", t, flags=re.IGNORECASE | re.MULTILINE):
            txt_list.append(t)

    return "...".join(txt_list) if txt_list else txt