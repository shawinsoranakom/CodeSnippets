def get_portfolio_data(
    dataset: str, frequency: str | None = None, measure: str | None = None
) -> tuple:
    """Get US portfolio data for a given dataset.

    Parameters
    ----------
    dataset : str
        The dataset to retrieve. Must be one of the available datasets in DATASET_CHOICES.
    frequency : Optional[str]
        The frequency of the data to return. Can be 'monthly', 'annual', or 'daily'.
        If None, defaults to 'monthly'.
    measure : Optional[str]
        The measure of the data to return.
        Can be 'value', 'equal', 'number_of_firms', or 'firm_size'.
        If None, defaults to 'value'.

    Returns
    -------
    tuple
        A tuple containing a list of pandas DataFrames and a list of metadata dictionaries.
        In most scenarios, there will only be 1 DataFrame and 1 metadata dictionary.

    Raises
    ------
    ValueError
        When an invalid combination of parameters or unsupported values are supplied.
    """
    if frequency and frequency.lower() not in ["monthly", "annual", "daily"]:
        raise ValueError(
            f"Frequency {frequency} not supported. Choose from 'monthly', 'annual', or 'daily'."
        )
    if measure and measure not in ["value", "equal", "number_of_firms", "firm_size"]:
        raise ValueError(
            f"Measure {measure} not supported. "
            + "Choose from 'value', 'equal', 'number_of_firms', or 'firm_size'."
        )
    if measure in ["number_of_firms", "firm_size"] and frequency == "annual":
        raise ValueError(
            f"Measure '{measure}' is only available for monthly frequency."
        )
    if "Factor" in dataset:
        measure = None

    file = download_file(dataset)
    table, desc = read_csv_file(file)
    dfs, metadata = process_csv_tables(table, desc)

    if frequency:
        out_dfs = [
            df
            for df, meta in zip(dfs, metadata)
            if meta["frequency"].lower() == frequency.lower()
        ]
        out_metadata = [
            meta for meta in metadata if meta["frequency"].lower() == frequency.lower()
        ]
    else:
        out_dfs = dfs
        out_metadata = metadata

    if measure is not None:
        if measure in ["value", "equal"]:
            out_dfs = [
                df
                for df, meta in zip(out_dfs, out_metadata)
                if "--" in meta["description"]
                and measure.lower() in meta["description"].split(" -- ")[0].lower()
            ]
            out_metadata = [
                meta
                for meta in out_metadata
                if "--" in meta["description"]
                and measure.lower() in meta["description"].split(" -- ")[0].lower()
            ]
        elif measure == "number_of_firms":
            out_dfs = [
                df
                for df, meta in zip(out_dfs, out_metadata)
                if "Number of Firms" in meta["description"]
            ]
            out_metadata = [
                meta
                for meta in out_metadata
                if "Number of Firms" in meta["description"]
            ]
        elif measure == "firm_size":
            out_dfs = [
                df
                for df, meta in zip(out_dfs, out_metadata)
                if "Average Firm Size" in meta["description"]
            ]
            out_metadata = [
                meta
                for meta in out_metadata
                if "Average Firm Size" in meta["description"]
            ]

    return out_dfs, out_metadata