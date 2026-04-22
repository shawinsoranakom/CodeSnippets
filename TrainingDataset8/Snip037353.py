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