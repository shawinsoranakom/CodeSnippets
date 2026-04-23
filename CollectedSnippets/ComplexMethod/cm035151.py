def _table_to_html(
        table, slide_part, image_counter_list: list, images: dict
    ) -> str:
        """Convert a PPTX table to an HTML table, handling merged cells and cell background images."""
        _BLIP_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
        _REL_NS = (
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
        )

        visited: set[tuple[int, int]] = set()
        html_parts = ["<table>"]

        for i, row in enumerate(table.rows):
            html_parts.append("<tr>")
            for j, cell in enumerate(row.cells):
                if (i, j) in visited:
                    continue
                tag = "th" if i == 0 else "td"
                attrs = ""
                if cell.is_merge_origin:
                    rs = cell.span_height
                    cs = cell.span_width
                    if cs > 1:
                        attrs += f' colspan="{cs}"'
                    if rs > 1:
                        attrs += f' rowspan="{rs}"'
                    for di in range(rs):
                        for dj in range(cs):
                            if (di, dj) != (0, 0):
                                visited.add((i + di, j + dj))

                content_parts = []

                # Extract cell background blip images
                blips = cell._tc.findall(f".//{_BLIP_NS}blip")
                for blip in blips:
                    r_embed = blip.get(f"{_REL_NS}embed")
                    if r_embed:
                        try:
                            image_part = slide_part.related_parts[r_embed]
                            image_counter_list[0] += 1
                            ext = image_part.content_type.split("/")[-1]
                            filename = f"image{image_counter_list[0]}.{ext}"
                            rel_path = f"images/{filename}"
                            images[rel_path] = image_part.blob
                            content_parts.append(
                                f'<img src="images/{filename}" width="100%">'
                            )
                        except (KeyError, AttributeError):
                            pass

                cell_text_parts = []
                for para in cell.text_frame.paragraphs:
                    # Check for math elements first
                    para_xml = para._p
                    if _paragraph_has_math(para_xml):
                        math_items = _extract_math_from_paragraph(para_xml)
                        for latex in math_items:
                            cell_text_parts.append(f"${latex}$")
                        continue

                    run_parts = []
                    for run in para.runs:
                        t = run.text or ""
                        if not t:
                            continue
                        try:
                            url = run.hyperlink.address
                        except Exception:
                            url = None

                        bold = bool(run.font.bold)
                        italic = bool(run.font.italic)
                        underline = bool(run.font.underline) and not url
                        strikethrough = bool(run.font.strike)
                        script = _pptx_run_script(run)

                        if bold:
                            t = f"<b>{t}</b>"
                        if italic:
                            t = f"<i>{t}</i>"
                        if underline:
                            t = f"<u>{t}</u>"
                        if strikethrough:
                            t = f"<del>{t}</del>"
                        if script == "super":
                            t = f"<sup>{t}</sup>"
                        elif script == "sub":
                            t = f"<sub>{t}</sub>"

                        if url:
                            run_parts.append(f'<a href="{url}">{t}</a>')
                        else:
                            run_parts.append(t)
                    cell_text_parts.append("".join(run_parts))
                text = "<br>".join(p for p in cell_text_parts if p.strip())
                if text:
                    content_parts.append(text)
                cell_html = "<br>".join(content_parts) if content_parts else ""

                html_parts.append(f"<{tag}{attrs}>{cell_html}</{tag}>")
            html_parts.append("</tr>")

        html_parts.append("</table>")
        return "\n".join(html_parts)