def _legacy_table(self, data: Data = None) -> "DeltaGenerator":
        """Display a static table.

        This differs from `st._legacy_dataframe` in that the table in this case is
        static: its entire contents are laid out directly on the page.

        Parameters
        ----------
        data : pandas.DataFrame, pandas.Styler, numpy.ndarray, Iterable, dict,
            or None
            The table data.

        Example
        -------
        >>> df = pd.DataFrame(
        ...    np.random.randn(10, 5),
        ...    columns=('col %d' % i for i in range(5)))
        ...
        >>> st._legacy_table(df)

        .. output::
           https://static.streamlit.io/0.25.0-2JkNY/index.html?id=KfZvDMprL4JFKXbpjD3fpq
           height: 480px

        """
        table_proto = DataFrameProto()
        marshall_data_frame(data, table_proto)
        return self.dg._enqueue("table", table_proto)