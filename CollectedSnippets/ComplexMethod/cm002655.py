def make_markdown_table(lines):
    """
    Create a nice Markdown table from the results in `lines`.
    """
    if lines is None or len(lines) == 0:
        return ""
    col_widths = {key: len(str(key)) for key in lines[0]}
    for line in lines:
        for key, value in line.items():
            if col_widths[key] < len(_maybe_round(value)):
                col_widths[key] = len(_maybe_round(value))

    table = _regular_table_line(list(lines[0].keys()), list(col_widths.values()))
    table += _second_table_line(list(col_widths.values()))
    for line in lines:
        table += _regular_table_line([_maybe_round(v) for v in line.values()], list(col_widths.values()))
    return table