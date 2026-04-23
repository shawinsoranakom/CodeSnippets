def _convert_body(doc, *, extract_drawings=True) -> tuple:
    """Traverse body elements in order and produce Markdown. Returns (markdown_str, images_dict)."""
    try:
        from docx.table import Table
        from docx.text.paragraph import Paragraph
    except ImportError:
        raise RuntimeError(
            "DOCX conversion requires python-docx: pip install paddleocr[doc2md]"
        )

    body_font_size = _get_body_font_size(doc)
    content_width = _get_content_width(doc)
    numbering_map = _build_numbering_map(doc)
    lines: list[str] = []
    images: dict = {}
    image_counter = [0]  # wrapped in list so inner functions can mutate it
    code_buf: list[str] = []  # buffer for consecutive code paragraphs
    toc_buf: list[tuple] = []  # buffer for consecutive TOC paragraphs
    ol_counters: dict[str, int] = {}  # key = "{numId}-{ilvl}", value = current index
    prev_was_list = False

    def flush_code_buf():
        """Flush the code buffer as a fenced code block."""
        if code_buf:
            lines.append("```")
            lines.extend(code_buf)
            lines.append("```")
            lines.append("")
            code_buf.clear()

    def flush_toc_buf():
        """Flush the TOC buffer as a Markdown list."""
        if toc_buf:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(_toc_entries_to_markdown(toc_buf))
            lines.append("")
            toc_buf.clear()

    field_state = _FieldState()
    for child in _flatten_body(doc.element.body):
        tag = child.tag.split("}")[-1]

        if tag == "p":
            para = Paragraph(child, doc)

            # TOC paragraph detection — before image extraction and other processing
            toc_level = _is_toc_paragraph(para)
            if toc_level is not None:
                toc_text = _extract_toc_text(para)
                if toc_text:
                    toc_anchor = _extract_toc_anchor(child)
                    toc_buf.append((toc_text, toc_anchor, toc_level))
                _update_field_state_for_paragraph(child, field_state)
                continue

            # Non-TOC paragraph: flush any buffered TOC entries
            flush_toc_buf()

            # Extract text box content for this paragraph element
            pending_textbox_lines = []
            if extract_drawings:
                tb_groups = _extract_textbox_paragraphs(child)
                if tb_groups:
                    pending_textbox_lines = _textbox_paragraphs_to_markdown(
                        tb_groups,
                        doc,
                        body_font_size,
                        image_counter,
                        images,
                        content_width,
                    )

            def _flush_textbox():
                if pending_textbox_lines:
                    if lines and lines[-1] != "":
                        lines.append("")
                    lines.extend(pending_textbox_lines)
                    lines.append("")

            # Extract images first
            img_list = _extract_images_from_paragraph(para, doc, image_counter)
            for filename, img_bytes, cx_emu in img_list:
                flush_code_buf()
                rel_path = f"images/{filename}"
                images[rel_path] = img_bytes
                if cx_emu and content_width:
                    pct = min(round(cx_emu / content_width * 100), 100)
                    lines.append(f'<img src="images/{filename}" width="{pct}%">')
                else:
                    lines.append(f'<img src="images/{filename}">')
                lines.append("")

            # Extract chart data tables
            chart_tables = _extract_chart_tables(para, doc)
            for chart_html in chart_tables:
                flush_code_buf()
                lines.append(chart_html)
                lines.append("")

            text = para.text.strip()

            # Math formula detection — must check before skipping empty-text paragraphs
            # (pure formula paragraphs have para.text == "")
            if _paragraph_has_math(para):
                flush_code_buf()
                if prev_was_list:
                    lines.append("")
                prev_was_list = False
                math_md = _paragraph_math_to_markdown(para)
                if math_md:
                    lines.append(math_md)
                    lines.append("")
                _flush_textbox()
                _update_field_state_for_paragraph(child, field_state)
                continue

            if not text:
                # Emit any _Toc bookmark anchors even for empty paragraphs.
                # Headings whose visible text comes from list numbering (not w:t
                # runs) have para.text == "" but still carry _Toc bookmarks that
                # TOC entries link to.
                for toc_bm in _extract_heading_toc_bookmarks(child):
                    lines.append(f'<a id="{toc_bm}"></a>')
                _flush_textbox()
                if not img_list and not pending_textbox_lines:
                    if code_buf:
                        code_buf.append("")  # preserve blank lines inside code blocks
                    elif lines and lines[-1] != "":
                        lines.append("")
                _update_field_state_for_paragraph(child, field_state)
                continue

            # Code paragraph: buffer it without heading/inline formatting
            if _is_code_paragraph(para):
                code_buf.append(para.text)
                _flush_textbox()
                _update_field_state_for_paragraph(child, field_state)
                continue

            # Non-code paragraph: flush any buffered code first
            flush_code_buf()

            level = _detect_heading_level(para, body_font_size)
            inline = _runs_to_markdown(_iter_paragraph_items(para, field_state)) or text

            if level > 0:
                # Strip outer **...** wrapping that headings may have inherited
                clean = inline.strip()
                if clean.startswith("**") and clean.endswith("**"):
                    clean = clean[2:-2]
                # Heading lines cannot span multiple source lines; revert <br>\n → <br>
                clean = clean.replace("<br>\n", "<br>")
                if prev_was_list:
                    lines.append("")
                prev_was_list = False
                # Add _Toc bookmark anchors if present (makes TOC links jumpable).
                # A heading may have multiple _Toc bookmarks from repeated TOC updates.
                for toc_bm in _extract_heading_toc_bookmarks(child):
                    lines.append(f'<a id="{toc_bm}"></a>')
                lines.append(f"{'#' * level} {clean}")
                lines.append("")
            else:
                list_info = _get_list_info(para, numbering_map)
                if list_info:
                    list_type, ilvl, num_id = list_info
                    indent = "    " * ilvl
                    if list_type == "ordered":
                        counter_key = f"{num_id}-{ilvl}"
                        ol_counters[counter_key] = ol_counters.get(counter_key, 0) + 1
                        prefix = f"{indent}{ol_counters[counter_key]}. "
                    else:
                        prefix = f"{indent}- "
                    if not prev_was_list and lines and lines[-1] != "":
                        lines.append("")
                    prev_was_list = True
                    # List item continuation lines need indentation; revert <br>\n → <br>
                    lines.append(prefix + inline.replace("<br>\n", "<br>"))
                else:
                    if prev_was_list:
                        lines.append("")
                    prev_was_list = False
                    # Reset ordered list counters when a list is interrupted
                    ol_counters.clear()
                    # Add _Toc bookmark anchors for non-heading paragraphs (e.g. Caption)
                    for toc_bm in _extract_heading_toc_bookmarks(child):
                        lines.append(f'<a id="{toc_bm}"></a>')
                    lines.append(inline)
                    lines.append("")

            _flush_textbox()

        elif tag == "tbl":
            flush_code_buf()
            flush_toc_buf()
            if prev_was_list:
                lines.append("")
            prev_was_list = False
            ol_counters.clear()
            table = Table(child, doc)
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(
                _table_to_html(table, doc, image_counter, images, content_width)
            )
            lines.append("")

    # Strip trailing blank lines
    flush_code_buf()
    flush_toc_buf()
    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines), images