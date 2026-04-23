def _iter_math_paragraph_parts(para) -> list:
    """Parse a paragraph with mixed text/math content into a list of parts.

    Returns a list where each element is either:
    - ("text", items_list) — a group of text runs to be formatted
    - ("display_math", latex_str) — a display math block ($$...$$)
    - ("inline_math", latex_str) — an inline math expression ($...$)
    """
    from docx.text.run import Run
    from docx.text.hyperlink import Hyperlink

    text_items = []
    parts = []

    def flush_text():
        if text_items:
            parts.append(("text", list(text_items)))
            text_items.clear()

    for child in para._element:
        tag = child.tag
        local = tag.split("}")[-1] if "}" in tag else tag

        if tag == f"{_M}oMathPara":
            flush_text()
            for omath in child.findall(f"{_M}oMath"):
                latex = _convert_omath(omath)
                if latex:
                    parts.append(("display_math", latex))
        elif tag == f"{_M}oMath":
            flush_text()
            latex = _convert_omath(child)
            if latex:
                parts.append(("inline_math", latex))
        elif local == "r":
            try:
                run = Run(child, para)
                if run.text:
                    text_items.append(
                        (
                            _effective_bold(run, para),
                            _effective_italic(run, para),
                            _effective_underline(run, para),
                            bool(run.font.strike),
                            _effective_superscript(run),
                            _effective_subscript(run),
                            run.text,
                            "",
                        )
                    )
            except Exception:
                pass
        elif local == "hyperlink":
            try:
                hl = Hyperlink(child, para)
                try:
                    url = hl.url or ""
                except (KeyError, AttributeError):
                    url = ""
                for run in hl.runs:
                    if run.text:
                        text_items.append(
                            (
                                _effective_bold(run, para),
                                _effective_italic(run, para),
                                False,
                                bool(run.font.strike),
                                _effective_superscript(run),
                                _effective_subscript(run),
                                run.text,
                                url,
                            )
                        )
            except Exception:
                pass

    flush_text()
    return parts