def _merge_continuation_tables(soup):
    """Merge consecutive tables where later ones are continuations."""
    tables = soup.find_all("table", recursive=True)
    tables_to_remove = set()

    i = 0
    while i < len(tables):
        table = tables[i]
        if table in tables_to_remove:
            i += 1
            continue

        # Find consecutive continuation tables.
        # Track last_ref so the proximity check is always between
        # adjacent tables (not base-vs-distant) when chaining
        # across multiple page-break boundaries.
        continuations = []
        j = i + 1
        last_ref = table
        while j < len(tables):
            next_table = tables[j]
            if next_table in tables_to_remove:
                j += 1
                continue
            # Check if next_table immediately follows (no significant content between)
            # and is a continuation table
            if _is_continuation_table(next_table, last_ref):
                continuations.append(next_table)
                last_ref = next_table
                j += 1
            else:
                break

        if continuations:
            # For each continuation, prepend header copies and append to main table
            for cont_table in continuations:
                # Get all rows from continuation table
                cont_rows = cont_table.find_all("tr")
                # Find the main table's tbody or create one
                tbody = table.find("tbody")

                if tbody is None:
                    tbody = table

                # Append continuation rows to main table
                for cont_row in cont_rows:
                    # Clone the row and append
                    tbody.append(cont_row.extract())

                # Mark for removal
                tables_to_remove.add(cont_table)

        i += 1

    # Remove merged tables
    for table in tables_to_remove:
        table.decompose()