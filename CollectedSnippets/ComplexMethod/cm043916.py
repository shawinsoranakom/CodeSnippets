def pivot_table_data(
    result: list[Any],
    country: str,
    limit: int | None,
    metadata: dict[str, Any],
) -> "pd.DataFrame":
    """Pivot table data based on whether hierarchy exists.

    This function determines whether to use indicator mode (simple pivot)
    or table mode (hierarchical pivot) based on the data.

    Parameters
    ----------
    result : list[Any]
        List of ImfEconomicIndicatorsData records to pivot.
    country : str
        Comma-separated country codes from the query.
    limit : int | None
        Maximum number of date columns to show.
    metadata : dict[str, Any]
        Metadata dictionary containing table information.

    Returns
    -------
    pd.DataFrame
        Pivoted DataFrame with appropriate structure.
    """
    # pylint: disable=import-outside-toplevel
    from pandas import DataFrame

    df = DataFrame(result)
    all_dates = sorted(df["date"].dropna().unique().tolist(), reverse=True)
    dates = all_dates[:limit] if limit is not None and limit > 0 else all_dates
    countries = sorted(df["country"].dropna().unique().tolist())

    # Check if any requested countries have no data for the selected dates
    # and warn the user
    if country and dates:
        requested_countries = [c.strip() for c in country.split(",")]
        check_missing_country_data(df, requested_countries, dates, countries)

    has_hierarchy = df["order"].notna().any() if "order" in df.columns else False

    if not has_hierarchy:
        return pivot_indicator_mode(df, dates, countries)

    return pivot_table_mode(df, dates, countries, metadata)