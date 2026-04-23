def read_csv_file(data: str):
    """Parse the raw data from a .csv file into a list of dictionaries representing tables.

    Note: This function is not intended for direct use, it is called by `get_portfolio_data`.
    """
    # pylint: disable=import-outside-toplevel
    import re

    lines = data.splitlines()
    tables: list = []
    general_description: list = []

    # Extract general description from the top of the file
    description_end_idx = 0
    for idx, line in enumerate(lines):
        if line.strip().startswith(",") or re.match(r"^\s*\d{4,6}", line):
            description_end_idx = idx
            break
        if line.strip():
            general_description.append(line.strip())

    # Extract initial table metadata from the last line of general description
    table_metadata: str = ""
    if general_description and (
        "Monthly" in general_description[-1]
        or "Annual" in general_description[-1]
        or "Returns" in general_description[-1]
    ):
        table_metadata = general_description[-1]
        general_description = general_description[:-1]

    general_desc_text = "\n".join(general_description)

    # Process tables in the file
    i = description_end_idx

    while i < len(lines):
        # Skip empty lines
        while i < len(lines) and not lines[i].strip():
            i += 1

        if i >= len(lines):
            break

        # Check if this is a table header (starts with comma)
        if lines[i].strip().startswith(","):
            # Look for metadata line before this header
            metadata = table_metadata  # Default to initial metadata
            j = i - 1
            while j >= description_end_idx:
                if lines[j].strip():
                    metadata = lines[j].strip()
                    break
                j -= 1

            # Parse headers
            header_line = lines[i].strip()
            headers = ["Date"] + header_line.split(",")[1:]

            # Move past header row
            i += 1

            # Collect data rows
            data_rows = []

            # Look for data rows until we hit the next header or end of file
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    break
                values = line.split(",")
                if values:
                    data_rows.append([d.strip() for d in values])

                i += 1

            # Add table if it has data
            if data_rows:
                tables.append(
                    {
                        "meta": metadata,
                        "headers": headers,
                        "rows": data_rows,
                        "is_annual": "Annual" in metadata,
                    }
                )

        # Check for standalone metadata
        elif "--" in lines[i] and any(
            d in lines[i] for d in ["Daily", "Monthly", "Annual", "Weekly"]
        ):
            # Update metadata for next table
            table_metadata = lines[i].strip()
            i += 1
        else:
            # Skip other lines
            i += 1

    return tables, general_desc_text