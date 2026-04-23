def _prepare_data_as_df(
        self, data: Union["DataFrame", "Series"] | None
    ) -> tuple["DataFrame", bool]:
        """Convert supplied data to a DataFrame."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.utils import basemodel_to_df, convert_to_basemodel
        from pandas import DataFrame, Series

        has_data = (isinstance(data, (Data, DataFrame, Series)) and not data.empty) or (bool(data))  # type: ignore
        index = (
            data.index.name
            if has_data and isinstance(data, (DataFrame, Series))
            else None
        )
        data_as_df: DataFrame = (
            basemodel_to_df(convert_to_basemodel(data), index=index)  # type: ignore
            if has_data
            else self._obbject.to_dataframe(index=index)  # type: ignore
        )
        if "date" in data_as_df.columns:
            data_as_df = data_as_df.set_index("date")
        if "provider" in data_as_df.columns:
            data_as_df.drop(columns="provider", inplace=True)
        return data_as_df, has_data