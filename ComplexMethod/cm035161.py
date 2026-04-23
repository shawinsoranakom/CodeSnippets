def _iter_paragraph_items(para, field_state=None) -> list:
    """Extract (bold, italic, underline, strikethrough, superscript, subscript, text, url) tuples from a paragraph in document order.

    Handles python-docx Hyperlink objects and w:fldChar field-code hyperlinks.
    Silently degrades to plain text on error.
    Note: underline is forced to False inside Hyperlink/field-hyperlink runs to avoid Word's default hyperlink underline style.

    field_state: optional _FieldState instance for cross-paragraph field tracking.
                 If None, a fresh _FieldState is created (single-paragraph mode).
    """
    if field_state is None:
        field_state = _FieldState()

    def _split_breaks(items):
        """Expand items containing \\n (from <w:br/> soft line breaks) into per-line items with <br> separators."""
        expanded = []
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
            if "\n" not in text:
                expanded.append(
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
                continue
            segments = text.split("\n")
            for j, seg in enumerate(segments):
                if seg:
                    expanded.append(
                        (
                            bold,
                            italic,
                            underline,
                            strikethrough,
                            superscript,
                            subscript,
                            seg,
                            url,
                        )
                    )
                if j < len(segments) - 1:
                    expanded.append(
                        (False, False, False, False, False, False, "<br>\n", "")
                    )
        return expanded

    try:
        from docx.text.hyperlink import Hyperlink
    except ImportError:
        return _split_breaks(
            [
                (
                    _effective_bold(r, para),
                    _effective_italic(r, para),
                    _effective_underline(r, para),
                    bool(r.font.strike),
                    _effective_superscript(r),
                    _effective_subscript(r),
                    r.text,
                    "",
                )
                for r in para.runs
                if r.text
            ]
        )

    items = []
    try:
        content_iter = para.iter_inner_content()
    except Exception:
        return _split_breaks(
            [
                (
                    _effective_bold(r, para),
                    _effective_italic(r, para),
                    _effective_underline(r, para),
                    bool(r.font.strike),
                    _effective_superscript(r),
                    _effective_subscript(r),
                    r.text,
                    "",
                )
                for r in para.runs
                if r.text
            ]
        )

    for element in content_iter:
        try:
            if isinstance(element, Hyperlink):
                try:
                    url = element.url or ""
                except (KeyError, AttributeError):
                    url = ""
                for run in element.runs:
                    if not run.text:
                        continue
                    # Force underline=False: Word's Hyperlink style adds underline by default
                    items.append(
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
                # Fallback: hyperlink with no runs but has text
                if not element.runs and element.text:
                    items.append(
                        (False, False, False, False, False, False, element.text, url)
                    )
            else:
                # Plain Run — check for fldChar control elements first
                fld_char = element._element.find(_W + "fldChar")
                if fld_char is not None:
                    fld_type = fld_char.get(_W + "fldCharType")
                    if fld_type == "begin":
                        if field_state.phase == "result":
                            field_state.nest_depth += 1
                        else:
                            field_state.active = True
                            field_state.phase = "instr"
                            field_state.url = None
                    elif fld_type == "separate":
                        if field_state.nest_depth == 0:
                            field_state.phase = "result"
                    elif fld_type == "end":
                        if field_state.nest_depth > 0:
                            field_state.nest_depth -= 1
                        else:
                            field_state.active = False
                            field_state.phase = None
                            field_state.url = None
                    continue

                instr_elem = element._element.find(_W + "instrText")
                if instr_elem is not None:
                    if field_state.active and field_state.phase == "instr":
                        # Extract HYPERLINK url from instrText
                        if instr_elem.text:
                            m = _RE_FIELD_HYPERLINK.search(instr_elem.text)
                            if m:
                                field_state.url = m.group(1)
                    continue  # Never emit instrText run as content

                # Plain Run
                if not element.text:
                    continue

                # If we are in the result phase of a field-code hyperlink, apply URL
                # and suppress underline (same as w:hyperlink element handling above).
                if (
                    field_state.phase == "result"
                    and field_state.nest_depth == 0
                    and field_state.url
                ):
                    items.append(
                        (
                            _effective_bold(element, para),
                            _effective_italic(element, para),
                            False,  # suppress underline for field hyperlinks
                            bool(element.font.strike),
                            _effective_superscript(element),
                            _effective_subscript(element),
                            element.text,
                            field_state.url,
                        )
                    )
                else:
                    items.append(
                        (
                            _effective_bold(element, para),
                            _effective_italic(element, para),
                            _effective_underline(element, para),
                            bool(element.font.strike),
                            _effective_superscript(element),
                            _effective_subscript(element),
                            element.text,
                            "",
                        )
                    )
        except Exception:
            continue

    return _split_breaks(items)