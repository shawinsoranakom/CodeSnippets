def clean_table_cells(rows):
    """Merge currency symbols and parentheses with values.

    Handles common SEC filing table patterns:
    - $ in one cell, value in next: "$" + "12,211" → "$12,211"
    - Opening paren with value: "(" + "2,257" + ")" → "(2,257)"
    - Split negative with note: "(2,257" + ")(b)" → "(2,257)(b)"
    - Value + trailing note: "7" + "(a)" → "7 (a)"
    """
    cleaned = []
    for row in rows:
        new_row = list(row)

        # Pass 1: Merge $ or ( prefix with following value
        i = 0
        while i < len(new_row):
            cell = new_row[i].strip()
            if cell in ["$", "(", "$(", "($"] and i + 1 < len(new_row):
                for j in range(i + 1, min(i + 4, len(new_row))):
                    next_val = new_row[j].strip()
                    if next_val and next_val not in ["$", ")", "%", ""]:
                        new_row[i] = cell + next_val
                        for k in range(i + 1, j + 1):
                            new_row[k] = ""
                        break
                    if next_val in [")", "%"]:
                        break
            i += 1

        # Pass 2: Merge split negatives like "(2,257" + ")(b)" or "(2,257" + ")"
        # Also handle "(2,257" + close paren in any form
        # And handle "$(171" + ")" patterns (currency + open paren)
        i = 0
        while i < len(new_row):
            cell = new_row[i].strip()
            # Check if cell has an open paren that isn't closed
            # Handles both "(2,257" and "$(171" patterns
            has_open_paren = "(" in cell and not cell.endswith(")")
            if has_open_paren and i + 1 < len(new_row):
                # Look for closing paren in following cells
                for j in range(i + 1, min(i + 3, len(new_row))):
                    next_val = new_row[j].strip()
                    if next_val.startswith(")"):
                        # Merge: "(2,257" + ")(b)" → "(2,257)(b)"
                        new_row[i] = cell + next_val
                        new_row[j] = ""
                        break
                    if next_val == "":
                        continue
                    break
            i += 1

        # Pass 3: Merge value with trailing ), %, pts., footnote markers (*, **)
        # SEC tables often split suffixes into narrow separate columns
        i = 0
        while i < len(new_row):
            cell = new_row[i].strip()
            if cell and i + 1 < len(new_row):
                for j in range(i + 1, min(i + 4, len(new_row))):
                    next_val = new_row[j].strip()
                    # Match suffix patterns: ), %, )%, %*, )pts., pts., *, **, etc.
                    if next_val and re.match(r"^[)%]*(?:pts\.?)?[*]*$", next_val):
                        new_row[i] = cell + next_val
                        for k in range(i + 1, j + 1):
                            new_row[k] = ""
                        break

                    if next_val and next_val not in ["", " "]:
                        break

            i += 1

        # Pass 4: Merge numeric value with following note like "(a)", "(b)"
        # Pattern: "7" + "(a)" → "7 (a)" or "5,754" + "(a)" → "5,754 (a)"
        i = 0

        while i < len(new_row):
            cell = new_row[i].strip()
            # Check if cell is a numeric value
            if (
                cell
                and re.match(r"^[\d,.$()-]+$", cell.replace(" ", ""))
                and i + 1 < len(new_row)
            ):
                next_val = new_row[i + 1].strip()
                # Check if next cell is a note reference like "(a)", "(b)"
                if next_val and re.match(r"^\([a-z]\)$", next_val):
                    new_row[i] = cell + " " + next_val
                    new_row[i + 1] = ""
            i += 1

        new_row = [c.strip() for c in new_row]
        cleaned.append(new_row)

    return cleaned