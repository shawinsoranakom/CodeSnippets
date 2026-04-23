def _parse_delimited(content: str, *, delimiter: str) -> Any:
    reader = csv.reader(io.StringIO(content), delimiter=delimiter)
    # csv.reader never yields [] — blank lines yield [""]. Filter out
    # rows where every cell is empty (i.e. truly blank lines).
    rows = [row for row in reader if _row_has_content(row)]
    if not rows:
        return content
    # If the declared delimiter produces only single-column rows, try
    # sniffing the actual delimiter — catches misidentified files (e.g.
    # a tab-delimited file with a .csv extension).
    if len(rows[0]) == 1:
        try:
            dialect = csv.Sniffer().sniff(content[:8192])
            if dialect.delimiter != delimiter:
                reader = csv.reader(io.StringIO(content), dialect)
                rows = [row for row in reader if _row_has_content(row)]
        except csv.Error:
            pass
    if rows and len(rows[0]) >= 2:
        return rows
    return content