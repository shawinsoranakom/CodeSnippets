def read_dat_file(data: str) -> list:
    """Parse the raw data from a .dat file into a list of dictionaries representing tables.

    Note: This function is not intended for direct use,
    it is called by `get_international_portfolio`.
    """
    # pylint: disable=import-outside-toplevel
    import re

    lines = data.splitlines()
    tables: list = []

    i = 0

    current_table: dict = {}
    while i < len(lines):
        # Check for table separator or new table metadata indicator
        if re.match(r"\s*,", lines[i]) or (
            i > 1
            and "Data" in lines[i]
            and "current_table" in locals()
            and current_table["rows"]
        ):
            # Add current table if it exists and has rows
            if "current_table" in locals() and current_table["rows"]:
                tables.append(current_table)

            # If this is a separator line, skip it
            if re.match(r"\s*,", lines[i]):
                i += 1
                continue

        # Start a new table
        current_table = {"meta": "", "spanners": "", "headers": [], "rows": []}
        meta_lines = []

        # Process metadata (which may span multiple lines)
        while i < len(lines):
            line = lines[i].strip()
            # Check if this line looks like the start of data or spanner rows
            if (
                "--" in line
                or "Firms" in line.split()
                and any(c.isdigit() for c in lines[i + 1])  # Spanner line
                if i + 1 < len(lines)
                else False  # Firms header
                or line in ["", " "]  # Empty separator
                or (line and line[0].isdigit() and len(line.split()) > 2)  # Data row
            ):
                break

            if line:  # Only add non-empty lines
                meta_lines.append(line)
            i += 1

        # Join all metadata lines
        current_table["meta"] = "\n".join(meta_lines)

        # Process spanners if we have a line with dashes
        if i < len(lines) and "--" in lines[i]:
            current_table["spanners"] = lines[i]
            i += 1
        else:
            # No spanners line found
            current_table["spanners"] = ""  # Empty spanners for tables like "Firms"

        # Process headers - handle special case for "Firms" tables
        if i < len(lines):
            header_line = lines[i].strip()
            # Check if this is a "Firms" table with its specific format
            if (
                "Firms" in header_line.split()
                or header_line
                and not header_line[0].isdigit()
            ):
                current_table["headers"] = ["Date"] + header_line.split()
                i += 1
            elif "Firms" in current_table["meta"]:
                # Default headers for Firms tables if header row is missing
                current_table["headers"] = [
                    "Date",
                    "Firms",
                    "B/M",
                    "E/P",
                    "CE/P",
                    "Yld",
                ]
            else:
                # Skip this table - malformed
                while i < len(lines) and not (
                    re.match(r"\s*,", lines[i]) or "Data" in lines[i]
                ):
                    i += 1
                continue

        # Process rows until next separator or next table start
        row_count = 0
        while i < len(lines) and not (
            re.match(r"\s*,", lines[i]) or "Data" in lines[i]
        ):
            # Skip copyright lines, empty lines, and other non-data lines
            if (
                lines[i].strip()
                and not lines[i].strip().startswith("Copyright")
                and "©" not in lines[i]
                and any(c.isdigit() for c in lines[i])
            ):  # Ensure line has at least one digit (likely a date)
                current_table["rows"].append(lines[i].split())
                row_count += 1
            i += 1

    # Add the last table if it has rows
    if "current_table" in locals() and current_table["rows"]:
        tables.append(current_table)

    return tables