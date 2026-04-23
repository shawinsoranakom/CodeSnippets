def _make_table(rows, headers):
    # compute display widths while ignoring ANSI codes
    cols = list(zip(*([headers] + rows))) if rows else [headers]
    widths = [max(len(_strip_ansi(x)) for x in col) for col in cols]
    header_line = " | ".join(_pad(h, w) for h, w in zip(headers, widths))
    sep_line = "-+-".join("-" * w for w in widths)
    body = [" | ".join(_pad(c, w) for c, w in zip(r, widths)) for r in rows]
    return "\n".join([header_line, sep_line] + body)