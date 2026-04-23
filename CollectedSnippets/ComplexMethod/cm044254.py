def df_to_basemodel(
    df: Union["DataFrame", "Series"], index: bool = False
) -> list[Data]:
    """Convert from a Pandas DataFrame to list of BaseModel."""
    # pylint: disable=import-outside-toplevel
    from pandas import MultiIndex, Series, to_datetime

    is_multiindex = isinstance(df.index, MultiIndex)

    if not is_multiindex and (index or df.index.name):
        df = df.reset_index()
    if isinstance(df, Series):
        df = df.to_frame()

    # Check if df has multiindex.  If so, add the index names to the df and a boolean column
    if isinstance(df.index, MultiIndex):
        df["is_multiindex"] = True
        df["multiindex_names"] = str(df.index.names)
        df = df.reset_index()

    # Converting to JSON will add T00:00:00.000 to all dates with no time element unless we format it as a string first.
    if "date" in df.columns:
        df["date"] = df["date"].apply(to_datetime)
        if all(t.time() == time(0, 0) for t in df["date"]):
            df["date"] = df["date"].apply(lambda x: x.date().strftime("%Y-%m-%d"))

    return [
        Data(**d) for d in json.loads(df.to_json(orient="records", date_format="iso"))
    ]