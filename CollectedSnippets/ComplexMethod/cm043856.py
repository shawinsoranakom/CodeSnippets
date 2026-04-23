def process_csv_tables(tables, general_description="") -> tuple:
    """Convert parsed table dictionaries from CSV files to pandas DataFrames.

    Note: This function is not intended for direct use, it is called by `get_portfolio_data`.
    """
    # pylint: disable=import-outside-toplevel
    import warnings  # noqa
    from pandas import DataFrame

    dataframes: list = []
    metadata: list = []

    for table_idx, table in enumerate(tables):
        # Skip empty tables
        if not table["rows"]:
            continue

        # Create DataFrame from rows
        rows_data = table.get("rows", [])
        headers = table["headers"]

        # Check if we have enough headers
        max_cols = max(len(row) for row in rows_data)
        if len(headers) < max_cols:
            headers.extend([f"Column_{i}" for i in range(len(headers), max_cols)])

        # Create dataframe with proper dimensions and headers
        df = DataFrame(rows_data)

        if df.empty or df.shape[1] == 0:
            continue

        # Set column names
        df.columns = headers[: df.shape[1]]

        # Convert Date column to datetime
        try:
            # Convert YYYYMM format to datetime
            df["Date"] = df.Date.apply(apply_date)
        except Exception as e:  # pylint: disable=W0718
            warnings.warn(f"Error parsing dates: {e}")
            df["Date"] = df["Date"].astype(str)

        # Set Date as index
        df = df.set_index("Date")
        df = df.sort_index()
        dataframes.append(df)

        # Get metadata from the table
        table_meta_desc = table["meta"].strip()

        # Determine frequency from the table's metadata
        frequency = "monthly"
        if "Annual" in table_meta_desc:
            frequency = "annual"

        # Create metadata entry
        table_meta = {
            "description": f"### {table_meta_desc}\n\n"
            + general_description.replace("\n", " ")
            + "\n\n",
            "frequency": frequency,
            "formations": headers[1:],
        }
        metadata.append(table_meta)

    return dataframes, metadata