def process_international_portfolio_data(tables: list, dividends: bool = True) -> tuple:
    """Convert parsed table dictionaries to pandas DataFrames with proper multi-index columns.

    Note: Not intended for direct use, this function is called by `get_international_portfolio`.
    """
    # pylint: disable=import-outside-toplevel
    import re  # noqa
    import warnings
    from pandas import DataFrame, MultiIndex

    dataframes: list = []
    metadata: list = []

    for table_idx, table in enumerate(tables):
        # Extract spanner groups
        spanner_groups = table["spanners"].replace("-", "").split()

        # Create DataFrame from rows
        rows_data = table.get("rows", [])
        df = DataFrame(rows_data)

        if df.empty:
            continue

        # Set column names based on headers
        headers = table["headers"]
        if len(headers) == len(df.columns):
            df.columns = headers

        # Check if this is a special case table with "Firms" column
        has_firms_column = "Firms" in df.columns

        # Parse and set Date column
        try:
            df["Date"] = df["Date"].apply(apply_date)
        except Exception as e:  # pylint: disable=W0718
            warnings.warn(f"Error parsing dates. Using string conversion. -> {e}")
            df["Date"] = df["Date"].astype(str)

        # Set Date as index (or Date and Mkt if applicable)
        df = (
            df.set_index(["Date", "Mkt"])
            if "Mkt" in df.columns and not has_firms_column
            else df.set_index("Date")
        )

        # Create multi-index columns only for regular tables (not those with Firms)
        if not has_firms_column and spanner_groups and len(df.columns) > 0:
            # Create multi-index columns
            remaining_headers = list(df.columns)
            bottom_level = remaining_headers

            # Calculate columns per group
            cols_per_group = len(remaining_headers) // len(spanner_groups)

            # Create top level for multi-index
            top_level = []
            for group in spanner_groups:
                top_level.extend([group] * cols_per_group)

            # Handle Zero column specially
            if "Zero" in remaining_headers:
                zero_idx = remaining_headers.index("Zero")
                # Find Yld group
                for group in spanner_groups:
                    if group.lower() == "yld":
                        # Ensure top_level has enough elements
                        while len(top_level) <= zero_idx:
                            top_level.append("")
                        top_level[zero_idx] = group
                        break

            # Create the multi-index columns
            if len(top_level) == len(bottom_level):
                df.columns = MultiIndex.from_arrays([top_level, bottom_level])

        dataframes.append(df)

        # Format metadata for description
        meta_text = table["meta"].strip().replace("\n", " - ")
        if dividends is False:
            meta_text += " - Ex-Dividends"

        # Format metadata nicely, replacing multiple spaces with a single space
        meta_text = re.sub(r"\s{2,}", " ", meta_text)

        is_annual = (
            df.index[0][0][-2:] in ["31", 31]
            if isinstance(df.index, MultiIndex)
            else df.index[0][-2:] in ["31", 31]
        )

        table_meta = {
            "description": meta_text,
            "frequency": "annual" if is_annual else "monthly",
            "formations": (
                [d for d in df.columns.tolist() if d != "Firms"]
                if has_firms_column
                else spanner_groups
            ),
        }
        metadata.append(table_meta)

    return dataframes, metadata