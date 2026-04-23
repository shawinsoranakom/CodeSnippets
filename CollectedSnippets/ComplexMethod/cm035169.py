def _textbox_paragraphs_to_markdown(
    textbox_groups, doc, body_font_size, image_counter, images, content_width
) -> list:
    """Convert text box paragraph groups to blockquote Markdown lines.

    Returns a list of strings (lines) to append to the main output.
    """
    try:
        from docx.text.paragraph import Paragraph
    except ImportError:
        return []

    output_lines = []
    for group_idx, para_elements in enumerate(textbox_groups):
        group_lines = []
        for p_elem in para_elements:
            try:
                para = Paragraph(p_elem, doc)

                # Handle images in text box
                img_list = _extract_images_from_paragraph(para, doc, image_counter)
                for filename, img_bytes, cx_emu in img_list:
                    rel_path = f"images/{filename}"
                    images[rel_path] = img_bytes
                    if cx_emu and content_width:
                        pct = min(round(cx_emu / content_width * 100), 100)
                        group_lines.append(
                            f'> <img src="images/{filename}" width="{pct}%">'
                        )
                    else:
                        group_lines.append(f'> <img src="images/{filename}">')

                # Handle math formulas
                if _paragraph_has_math(para):
                    math_md = _paragraph_math_to_markdown(para)
                    if math_md:
                        group_lines.append(f"> {math_md}")
                    continue

                # Plain inline text (no heading/list/code detection for text boxes)
                inline = _runs_to_markdown(_iter_paragraph_items(para))
                if not inline:
                    inline = para.text.strip()
                if inline:
                    group_lines.append(f"> {inline}")
            except Exception:
                continue

        if group_lines:
            if output_lines:
                output_lines.append("")
            output_lines.extend(group_lines)

    return output_lines