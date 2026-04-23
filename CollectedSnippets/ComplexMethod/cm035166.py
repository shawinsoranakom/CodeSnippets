def _table_to_html(
    table, doc, image_counter: list, images: dict, content_width: int = 0
) -> str:
    """Convert a python-docx Table to an HTML table, handling merged cells and inline images."""
    grid = [[cell for cell in row.cells] for row in table.rows]
    nrows = len(grid)
    if nrows == 0:
        return ""
    ncols = len(grid[0])

    visited: set[tuple[int, int]] = set()
    html_parts = ["<table>"]

    for i in range(nrows):
        html_parts.append("<tr>")
        for j in range(ncols):
            if (i, j) in visited:
                continue
            tc = grid[i][j]._tc
            # Compute colspan
            colspan = 1
            while j + colspan < ncols and grid[i][j + colspan]._tc is tc:
                visited.add((i, j + colspan))
                colspan += 1
            # Compute rowspan
            rowspan = 1
            while i + rowspan < nrows and grid[i + rowspan][j]._tc is tc:
                for k in range(colspan):
                    visited.add((i + rowspan, j + k))
                rowspan += 1

            cell = grid[i][j]
            content_parts = []
            for para in cell.paragraphs:
                img_list = _extract_images_from_paragraph(para, doc, image_counter)
                for filename, img_bytes, cx_emu in img_list:
                    rel_path = f"images/{filename}"
                    images[rel_path] = img_bytes
                    if cx_emu and content_width:
                        pct = min(round(cx_emu / content_width * 100), 100)
                        content_parts.append(
                            f'<img src="images/{filename}" width="{pct}%">'
                        )
                    else:
                        content_parts.append(f'<img src="images/{filename}">')
                para_html = (
                    _paragraph_math_to_html(para).strip()
                    if _paragraph_has_math(para)
                    else _runs_to_html(_iter_paragraph_items(para)).strip()
                    or para.text.strip()
                )
                if para_html:
                    content_parts.append(para_html)
                # Extract text box content from table cell paragraph
                try:
                    tb_groups = _extract_textbox_paragraphs(para._element)
                    for tb_paras in tb_groups:
                        for tb_p in tb_paras:
                            tb_t_elems = tb_p.findall(f".//{_W}t")
                            tb_text = "".join(
                                t.text for t in tb_t_elems if t.text
                            ).strip()
                            if tb_text:
                                content_parts.append(f"[{tb_text}]")
                except Exception:
                    pass
            cell_html = "<br>".join(content_parts) if content_parts else ""

            is_header = False
            trPr = table.rows[i]._tr.find(f"{_W}trPr")
            if trPr is not None:
                tbl_header = trPr.find(f"{_W}tblHeader")
                if tbl_header is not None:
                    val = tbl_header.get(f"{_W}val")
                    is_header = val is None or val.lower() not in ("false", "0", "off")
            if not is_header and i == 0 and nrows > 1:
                is_header = (
                    True  # fallback: treat first row as header in multi-row tables
                )
            tag = "th" if is_header else "td"
            attrs = ""
            if colspan > 1:
                attrs += f' colspan="{colspan}"'
            if rowspan > 1:
                attrs += f' rowspan="{rowspan}"'
            html_parts.append(f"<{tag}{attrs}>{cell_html}</{tag}>")
        html_parts.append("</tr>")

    html_parts.append("</table>")
    return "\n".join(html_parts)