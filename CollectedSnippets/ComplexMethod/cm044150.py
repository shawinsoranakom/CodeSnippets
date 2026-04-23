def table(
        self,
        data: Union["DataFrame", "Series"] | None = None,
        title: str = "",
        include_query_toolbar: bool = True,
    ):
        """Display an interactive table.

        Parameters
        ----------
        data : Optional[Union[DataFrame, Series]], optional
            Data to be plotted, by default None.
            If no data is provided the OBBject results will be used.
        title : str, optional
            Title of the table, by default "".
        include_query_toolbar : bool, optional
            Whether to include the Pandas Query toolbar, by default True.
        """
        # pylint: disable=import-outside-toplevel
        from pandas import RangeIndex

        data_as_df, _ = self._prepare_data_as_df(data)
        if isinstance(data_as_df.index, RangeIndex):
            data_as_df.reset_index(inplace=True, drop=True)
        else:
            data_as_df.reset_index(inplace=True)
        for col in data_as_df.columns:
            data_as_df[col] = data_as_df[col].apply(self._convert_to_string)
        try:
            send_table = getattr(self._backend, "send_table")
            if include_query_toolbar:
                send_table(
                    df_table=data_as_df,
                    title=title
                    or self._obbject._route  # pylint: disable=protected-access
                    or "",
                    theme=self._charting_settings.table_style,  # pylint: disable=protected-access
                )
            else:
                send_table(
                    df_table=data_as_df,
                    title=title
                    or self._obbject._route  # pylint: disable=protected-access
                    or "",
                    theme=self._charting_settings.table_style,  # pylint: disable=protected-access
                    include_query_toolbar=False,
                )
        except Exception as e:  # pylint: disable=W0718
            warn(f"Failed to show table with backend. {e}")