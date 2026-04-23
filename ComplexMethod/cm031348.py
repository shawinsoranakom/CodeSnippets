def layout_content_lines(
    lines: tuple[ContentLine, ...],
    width: int,
    start_offset: int,
) -> LayoutResult:
    """Wrap content lines to fit *width* columns.

    A short line passes through as one ``WrappedRow``; a long line is
    split at the column boundary with ``\\`` markers::

        >>> short = 1           ← one WrappedRow
        >>> x = "a long stri\\  ← two WrappedRows, first has suffix="\\"
        ng"
    """
    if width <= 0:
        return LayoutResult((), LayoutMap(()), ())

    offset = start_offset
    wrapped_rows: list[WrappedRow] = []
    layout_rows: list[LayoutRow] = []
    line_end_offsets: list[int] = []

    for line in lines:
        newline_advance = int(line.source.has_newline)
        for leading in line.prompt.leading_lines:
            line_end_offsets.append(offset)
            wrapped_rows.append(
                WrappedRow(
                    fragments=(leading,),
                )
            )
            layout_rows.append(LayoutRow(0, (), buffer_advance=0))

        prompt_text = line.prompt.text
        prompt_width = line.prompt.width
        body = tuple(line.body)
        body_widths = tuple(fragment.width for fragment in body)

        # Fast path: line fits on one row.
        if not body_widths or (sum(body_widths) + prompt_width) < width:
            offset += len(body) + newline_advance
            line_end_offsets.append(offset)
            wrapped_rows.append(
                WrappedRow(
                    prompt_text=prompt_text,
                    prompt_width=prompt_width,
                    fragments=body,
                    layout_widths=body_widths,
                    buffer_advance=len(body) + newline_advance,
                )
            )
            layout_rows.append(
                LayoutRow(
                    prompt_width,
                    body_widths,
                    buffer_advance=len(body) + newline_advance,
                )
            )
            continue

        # Slow path: line needs wrapping.
        current_prompt = prompt_text
        current_prompt_width = prompt_width
        start = 0
        total = len(body)
        while True:
            # Find how many characters fit on this row.
            index_to_wrap_before = 0
            column = 0
            for char_width in body_widths[start:]:
                if column + char_width + current_prompt_width >= width:
                    break
                index_to_wrap_before += 1
                column += char_width

            if index_to_wrap_before == 0 and start < total:
                index_to_wrap_before = 1  # force progress

            at_line_end = (start + index_to_wrap_before) >= total
            if at_line_end:
                offset += index_to_wrap_before + newline_advance
                suffix = ""
                suffix_width = 0
                buffer_advance = index_to_wrap_before + newline_advance
            else:
                offset += index_to_wrap_before
                suffix = "\\"
                suffix_width = 1
                buffer_advance = index_to_wrap_before

            end = start + index_to_wrap_before
            row_fragments = body[start:end]
            row_widths = body_widths[start:end]
            line_end_offsets.append(offset)
            wrapped_rows.append(
                WrappedRow(
                    prompt_text=current_prompt,
                    prompt_width=current_prompt_width,
                    fragments=row_fragments,
                    layout_widths=row_widths,
                    suffix=suffix,
                    suffix_width=suffix_width,
                    buffer_advance=buffer_advance,
                )
            )
            layout_rows.append(
                LayoutRow(
                    current_prompt_width,
                    row_widths,
                    suffix_width=suffix_width,
                    buffer_advance=buffer_advance,
                )
            )

            start = end
            current_prompt = ""
            current_prompt_width = 0
            if at_line_end:
                break

    return LayoutResult(
        tuple(wrapped_rows),
        LayoutMap(tuple(layout_rows)),
        tuple(line_end_offsets),
    )