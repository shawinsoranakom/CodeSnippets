def last_index_for_melted_dataframes(
    data: Union["DataFrameCompatible", Any]
) -> Optional[Hashable]:
    if type_util.is_dataframe_compatible(data):
        data = type_util.convert_anything_to_df(data)

        if data.index.size > 0:
            return cast(Hashable, data.index[-1])

    return None