def extract_markdown_tables(text_content):
    """
    Extract all markdown tables from text content.
    Returns a list of tables, where each table is a list of rows,
    and each row is a list of cell values.
    """
    tables = []
    lines = text_content.split("\n")
    current_table = []
    in_table = False

    for line in lines:
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            # Skip separator rows (contain only dashes and pipes)
            if re.match(r"^\|[\s\-|]+\|$", line):
                continue
            # Parse cells from the row
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            current_table.append(cells)
            in_table = True
        else:
            if in_table and current_table:
                tables.append(current_table)
                current_table = []
            in_table = False

    # Don't forget the last table
    if current_table:
        tables.append(current_table)

    return tables