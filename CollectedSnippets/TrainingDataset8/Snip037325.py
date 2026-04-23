def _maybe_melt_data_for_add_rows(
    data: DFT,
    delta_type: str,
    last_index: Any,
) -> Tuple[Union[DFT, "DataFrame"], Union[int, Any]]:
    import pandas as pd

    def _melt_data(
        df: "DataFrame", last_index: Any
    ) -> Tuple["DataFrame", Union[int, Any]]:
        if isinstance(df.index, pd.RangeIndex):
            old_step = _get_pandas_index_attr(df, "step")

            # We have to drop the predefined index
            df = df.reset_index(drop=True)

            old_stop = _get_pandas_index_attr(df, "stop")

            if old_step is None or old_stop is None:
                raise StreamlitAPIException(
                    "'RangeIndex' object has no attribute 'step'"
                )

            start = last_index + old_step
            stop = last_index + old_step + old_stop

            df.index = pd.RangeIndex(start=start, stop=stop, step=old_step)
            last_index = stop - 1

        index_name = df.index.name
        if index_name is None:
            index_name = "index"

        df = pd.melt(df.reset_index(), id_vars=[index_name])
        return df, last_index

    # For some delta types we have to reshape the data structure
    # otherwise the input data and the actual data used
    # by vega_lite will be different, and it will throw an error.
    if (
        delta_type in DELTA_TYPES_THAT_MELT_DATAFRAMES
        or delta_type in ARROW_DELTA_TYPES_THAT_MELT_DATAFRAMES
    ):
        if not isinstance(data, pd.DataFrame):
            return _melt_data(
                df=type_util.convert_anything_to_df(data),
                last_index=last_index,
            )
        else:
            return _melt_data(df=data, last_index=last_index)

    return data, last_index