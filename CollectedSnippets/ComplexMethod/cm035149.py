def _process_shape(
        self, shape, slide_parts, images, image_counter, slide_width, slide_part
    ):
        """Recursively process a shape: Picture, GroupShape, Chart, Table, or TextFrame."""
        Picture = self._Picture
        MSO_SHAPE_TYPE = self._MSO_SHAPE_TYPE

        # 1. Picture
        if isinstance(shape, Picture):
            try:
                img = shape.image
                image_counter[0] += 1
                filename = f"image{image_counter[0]}.{img.ext}"
                rel_path = f"images/{filename}"
                images[rel_path] = img.blob
                if shape.width and slide_width:
                    pct = min(round(shape.width / slide_width * 100), 100)
                    slide_parts.append(f'<img src="images/{filename}" width="{pct}%">')
                else:
                    slide_parts.append(f'<img src="images/{filename}">')
            except (ValueError, AttributeError):
                pass
            return

        # 2. GroupShape - recurse into child shapes
        if MSO_SHAPE_TYPE and shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            try:
                for child in shape.shapes:
                    self._process_shape(
                        child,
                        slide_parts,
                        images,
                        image_counter,
                        slide_width,
                        slide_part,
                    )
            except AttributeError:
                pass
            return

        # 3. Chart
        if shape.has_chart:
            slide_parts.append(self._chart_to_html(shape.chart))
            return

        # 4. Table
        if shape.has_table:
            slide_parts.append(
                self._table_to_html(shape.table, slide_part, image_counter, images)
            )
            return

        # 5. TextFrame
        if shape.has_text_frame:
            for paragraph in shape.text_frame.paragraphs:
                # Check for math elements first
                para_xml = paragraph._p
                if _paragraph_has_math(para_xml):
                    math_items = _extract_math_from_paragraph(para_xml)
                    for latex in math_items:
                        slide_parts.append(f"$$\n{latex}\n$$")
                    continue

                parts = []
                for run in paragraph.runs:
                    t = run.text
                    if not t:
                        continue
                    try:
                        url = run.hyperlink.address
                    except Exception:
                        url = None

                    bold = bool(run.font.bold)
                    italic = bool(run.font.italic)
                    underline = bool(run.font.underline) and not url
                    strikethrough = _pptx_run_strike(run)
                    script = _pptx_run_script(run)

                    if "\n" in t:
                        segments = t.split("\n")
                        for j, seg in enumerate(segments):
                            if seg:
                                parts.append(
                                    _format_run_segment(
                                        seg,
                                        bold,
                                        italic,
                                        underline,
                                        strikethrough,
                                        script,
                                        url,
                                    )
                                )
                            if j < len(segments) - 1:
                                parts.append("<br>\n")
                    else:
                        parts.append(
                            _format_run_segment(
                                t, bold, italic, underline, strikethrough, script, url
                            )
                        )
                text = "".join(parts).strip()
                if not text:
                    continue
                level = paragraph.level
                indent = "  " * level
                # List item continuation lines need indentation; revert <br>\n → <br>
                text = text.replace("<br>\n", "<br>")
                slide_parts.append(f"{indent}- {text}")