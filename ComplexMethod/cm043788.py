def parse_row_semantic(row, num_expected_cols=0):
    """Parse a row into (label, values) like non_xbrl_parser does."""
    label = None
    values = []
    additional_text = []  # Text that might be values if no numeric values found

    for cell in row:
        c = cell.strip()

        if not c or c == "$":
            continue

        # Em dashes represent "not applicable" - they're values
        # Handle plain dashes AND dollar+dash like "$—" or "$ —" (spaced)
        if c in ("—", "–", "-") and len(c) == 1 or re.match(r"^\$\s*[—–\-]$", c):
            values.append(c)
        # Check if this is a number (with optional $ prefix, commas, parens for negative)

        elif re.match(
            r"^[+\-]?[\$]?\s*\(?[\$]?\s*\d[\d,]*\.?\d*\s*\)?\s*%?(?:pts\.?)?\s*\*{0,2}\s*(\(\d+\)|\([a-z]\))?$",
            c.replace(",", ""),
        ):
            # It's a number (possibly with footnote) - it's a value
            values.append(c)
        elif label is None:
            label = c
        else:
            # Additional text - might be a text value (like credit ratings)
            # Keep it separate so we can decide later
            additional_text.append(c)

    # If we found no numeric values but have additional text, and we expect columns,
    # treat the additional text as values (e.g., credit ratings like "P-1", "A1")
    if not values and additional_text and num_expected_cols > 0:
        # Use additional text as values (up to expected count)
        values = additional_text[:num_expected_cols]
    elif not values and additional_text:
        # No expected columns info - append to label as before
        label = (label or "") + " " + " ".join(additional_text)
    elif (
        values
        and additional_text
        and len(values) < num_expected_cols
        and num_expected_cols > 0
    ):
        # We have some numeric values but fewer than expected. Fill remaining
        # slots with extra text items — e.g., a "Valuation Technique" text
        # column that appears alongside a numeric "Fair Value" column.
        needed = num_expected_cols - len(values)
        values.extend(additional_text[:needed])

    # If we have values but no label, it's likely a total row
    # Use "Total" as the label if values look like currency totals
    if values and not label:
        # Check if values contain dollar amounts (start with $ or have commas)
        has_currency = any(
            v.startswith("$") or re.match(r"^\(?\d{1,3}(,\d{3})+", v) for v in values
        )
        if has_currency:
            label = "Total"

    return label, values