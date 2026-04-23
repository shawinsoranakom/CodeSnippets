def get_international_portfolio(
    index: str | None = None,
    country: str | None = None,
    dividends: bool = True,
    frequency: str | None = None,
    measure: str | None = None,
    all_data_items_required: bool | None = None,
) -> tuple:
    """Get the international portfolio data for a given index or country.

    Parameters
    ----------
    index : Optional[str]
        The index for which to get the portfolio data. If None, country must be provided.
    country : Optional[str]
        The country for which to get the portfolio data. If None, index must be provided.
    dividends : bool
        When False, returns data with dividends excluded. Defaults to True.
    frequency : Optional[str]
        The frequency of the data to return. Can be 'monthly', or 'annual'.
        If None, defaults to 'monthly'.
    measure : Optional[str]
        The measure of the data to return. Can be 'usd', 'local', or 'ratios'.
        If None, defaults to 'usd'.
    all_data_items_required : Optional[bool]
        Default is True.
        If True, returns only data for firms with all 4 ratios of B/M, E/P, CE/P, and Yld.
        When False, returns data for firms with B/M data only.

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
    measure = measure.lower() if measure is not None else "usd"
    data = get_international_portfolio_data(index, country, dividends)
    tables = read_dat_file(data)
    dataframes, metadata = process_international_portfolio_data(tables, dividends)

    if measure and measure not in ["usd", "local", "ratios"]:
        raise ValueError(
            f"Measure {measure} not supported. Choose from 'usd', 'local', or 'ratios'."
        )

    if frequency == "monthly" and measure == "ratios":
        raise ValueError("Only annual frequency is available for 'ratios' measure.")

    if frequency:
        dfs = [
            df
            for df, meta in zip(dataframes, metadata)
            if meta["frequency"] == frequency
        ]
        dfs_meta = [meta for meta in metadata if meta["frequency"] == frequency]
    else:
        dfs = dataframes
        dfs_meta = metadata

    if measure == "local":
        dfs = [df for df, meta in zip(dfs, dfs_meta) if "Local" in meta["description"]]
        dfs_meta = [meta for meta in dfs_meta if "Local" in meta["description"]]
    elif measure == "usd":
        dfs = [df for df, meta in zip(dfs, dfs_meta) if "Dollar" in meta["description"]]
        dfs_meta = [meta for meta in dfs_meta if "Dollar" in meta["description"]]
    elif measure == "ratios":
        dfs = [df for df, meta in zip(dfs, dfs_meta) if "Ratios" in meta["description"]]
        dfs_meta = [meta for meta in dfs_meta if "Ratios" in meta["description"]]

    if all_data_items_required is False and measure != "ratios":
        dfs = [
            df
            for df, meta in zip(dfs, dfs_meta)
            if "Not Reqd" not in meta["description"]
        ]
        dfs_meta = [
            meta
            for meta in dfs_meta
            if meta.get("description", "").endswith("Not Reqd")
        ]
    elif all_data_items_required is True:
        dfs = [
            df for df, meta in zip(dfs, dfs_meta) if "Required" in meta["description"]
        ]
        dfs_meta = [meta for meta in dfs_meta if "Required" in meta["description"]]

    return dfs, dfs_meta