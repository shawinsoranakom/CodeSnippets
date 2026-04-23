def basemodel_to_df(
    data: list[Data] | Data,
    index: str | None = None,
) -> "DataFrame":
    """Convert list of BaseModel to a Pandas DataFrame."""
    # pylint: disable=import-outside-toplevel
    from pandas import DataFrame, to_datetime

    if isinstance(data, list):
        df = DataFrame(
            [d.model_dump(exclude_none=True, exclude_unset=True) for d in data]
        )
    else:
        try:
            df = DataFrame(data.model_dump(exclude_none=True, exclude_unset=True))
        except ValueError:
            df = DataFrame(
                data.model_dump(exclude_none=True, exclude_unset=True), index=["values"]
            )

    if "is_multiindex" in df.columns:
        col_names = ast.literal_eval(df.multiindex_names.unique()[0])
        df = df.set_index(col_names)
        df = df.drop(["is_multiindex", "multiindex_names"], axis=1)

    # If the date column contains dates only, convert them to a date to avoid encoding time data.
    if "date" in df.columns:
        df["date"] = df["date"].apply(to_datetime)
        if all(t.time() == time(0, 0) for t in df["date"]):
            df["date"] = df["date"].apply(lambda x: x.date())

    if index and index in df.columns:
        if index == "date":
            df.set_index("date", inplace=True)
            df.sort_index(axis=0, inplace=True)
        else:
            df = df.set_index(index) if index and index in df.columns else df

    return df