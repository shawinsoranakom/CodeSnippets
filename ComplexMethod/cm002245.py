def _format_table(headers: list[str], rows: list[tuple[str, ...] | None], row_styles: list[str] | None = None) -> str:
    if not rows:
        return f"{ANSI_ROW}(no matches){ANSI_RESET}"

    widths = [len(header) for header in headers]
    for row in rows:
        if row is None:
            continue
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    header_line = " | ".join(header.ljust(widths[idx]) for idx, header in enumerate(headers))
    divider = "-+-".join("-" * widths[idx] for idx in range(len(headers)))
    total_width = sum(widths) + 3 * (len(headers) - 1)

    styled_rows = []
    style_idx = 0
    for row in rows:
        if row is None:
            styled_rows.append(f"{ANSI_SECTION}{'-' * total_width}{ANSI_RESET}")
            continue

        line = " | ".join(cell.ljust(widths[col_idx]) for col_idx, cell in enumerate(row))
        style = ANSI_ROW
        if row_styles and style_idx < len(row_styles) and row_styles[style_idx]:
            style = row_styles[style_idx]
        styled_rows.append(f"{style}{line}{ANSI_RESET}")
        style_idx += 1

    return "\n".join([f"{ANSI_SECTION}{header_line}{ANSI_RESET}", divider] + styled_rows)