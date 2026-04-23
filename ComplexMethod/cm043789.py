def detect_and_merge_multiindex_headers(data_rows):
    """Detect and merge multi-index column headers from data rows.

    Returns (header_rows, data_start_index, num_value_cols) where:
        header_rows: list of COMPRESSED header rows [label_col, val1, val2, ...]
        data_start_index: index into data_rows where actual data begins
        num_value_cols: number of value columns (for data extraction)
    """
    if not data_rows or len(data_rows) < 3:
        return None, 0, 0

    def is_year(t):
        # Strip trailing footnote markers like *, **, †, ‡, §
        t_clean = re.sub(r"[*†‡§+]+$", "", t.strip())
        return bool(re.match(r"^(19|20)\d{2}$", t_clean))

    def is_all_caps_word(t):
        t = t.strip()
        return bool(re.match(r"^[A-Z]{2,}$", t)) and len(t) > 1

    def is_numeric(t):
        t = t.strip()
        return bool(re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t)) and any(
            c.isdigit() for c in t
        )

    def row_has_years(row):
        non_empty = [c.strip() for c in row if c.strip()]
        year_count = sum(1 for c in non_empty if is_year(c))
        return year_count >= 3  # At least 3 years

    def row_is_all_caps_categories(row):
        non_empty = [c.strip() for c in row if c.strip()]
        if len(non_empty) < 2:
            return False
        caps_count = sum(1 for c in non_empty if is_all_caps_word(c))
        return caps_count >= 2 and caps_count >= len(non_empty) * 0.5

    def row_has_data(row):
        return any(is_numeric(c) for c in row)

    def row_is_title(row):
        non_empty = [c.strip() for c in row if c.strip()]

        if not non_empty:
            return True

        row_text = " ".join(non_empty)

        return bool(
            re.search(
                r"(years?\s+ended|months?\s+ended|weeks?\s+ended|unaudited|as\s+of|income\s+statement|balance\s+sheet|statement\s+of)",
                row_text,
                re.I,
            )
        )

    # Scan for header structure
    category_rows_data = []  # List of (row_idx, [cat_texts])
    year_row_idx = None
    years_list = []  # Actual year values in order
    data_start = 0

    for i, row in enumerate(data_rows):
        # Check for year row FIRST (before data check, since years look numeric)
        if row_has_years(row):
            year_row_idx = i
            years_list = [c.strip() for c in row if c.strip() and is_year(c.strip())]
            data_start = i + 1
            continue  # Keep scanning to find where data actually starts

        if row_has_data(row):
            data_start = i
            break

        if row_is_title(row):
            continue

        if row_is_all_caps_categories(row):
            # Extract category texts
            cats = [c.strip() for c in row if c.strip() and is_all_caps_word(c.strip())]
            category_rows_data.append((i, cats))

    if year_row_idx is None or not years_list:
        return None, 0, 0

    num_years = len(years_list)

    # Merge category rows vertically
    # EQUIPMENT + OPERATIONS = "EQUIPMENT OPERATIONS"
    # FINANCIAL + SERVICES = "FINANCIAL SERVICES"
    # Build categories by position (first row gives base, subsequent rows add)
    if category_rows_data:
        # Use max categories from any row
        max_cats = max(len(cats) for _, cats in category_rows_data)
        merged_categories = [""] * max_cats

        for _, cats in category_rows_data:
            for j, cat in enumerate(cats):
                if j < len(merged_categories):
                    if merged_categories[j]:
                        merged_categories[j] += " " + cat
                    else:
                        merged_categories[j] = cat
                else:
                    merged_categories.append(cat)

        num_categories = len(merged_categories)
    else:
        # No ALL CAPS categories found - return None to use fallback
        # which can detect Title Case categories like "Pensions", "OPEB"
        # via colspan analysis in extract_periods_from_rows
        return None, 0, 0

    # Calculate years per category
    years_per_cat = num_years // num_categories
    if years_per_cat == 0:
        years_per_cat = 1

    # Build COMPRESSED headers
    # Format: ["", "CAT1", "", "", "CAT2", "", "", ...]  (category in first cell of span)
    # Format: ["", "2025", "2024", "2023", "2025", "2024", "2023", ...]

    cat_row = [""]  # Label column
    year_row = [""]  # Label column

    year_idx = 0
    for cat in merged_categories:
        # Category name in first cell
        cat_row.append(cat)
        # Empty cells for remaining years under this category
        for _ in range(years_per_cat - 1):
            cat_row.append("")

        # Years for this category
        for _ in range(years_per_cat):
            if year_idx < num_years:
                year_row.append(years_list[year_idx])
                year_idx += 1
            else:
                year_row.append("")

    header_rows = [cat_row, year_row]
    num_value_cols = num_categories * years_per_cat

    # Find actual data start
    for i in range(data_start, len(data_rows)):
        row = data_rows[i]
        if row_has_data(row):
            data_start = i
            break
        if (
            not row_is_title(row)
            and not row_is_all_caps_categories(row)
            and not row_has_years(row)
        ):
            data_start = i
            break

    return header_rows, data_start, num_value_cols