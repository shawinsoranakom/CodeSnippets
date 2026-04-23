def _arrow_add_rows(
        self: DG,
        data: "Data" = None,
        **kwargs: Union[
            "DataFrame", "npt.NDArray[Any]", Iterable[Any], Dict[Hashable, Any], None
        ],
    ) -> Optional[DG]:
        """Concatenate a dataframe to the bottom of the current one.

        Parameters
        ----------
        data : pandas.DataFrame, pandas.Styler, numpy.ndarray, Iterable, dict, or None
            Table to concat. Optional.

        **kwargs : pandas.DataFrame, numpy.ndarray, Iterable, dict, or None
            The named dataset to concat. Optional. You can only pass in 1
            dataset (including the one in the data parameter).

        Example
        -------
        >>> df1 = pd.DataFrame(
        ...    np.random.randn(50, 20),
        ...    columns=('col %d' % i for i in range(20)))
        ...
        >>> my_table = st._arrow_table(df1)
        >>>
        >>> df2 = pd.DataFrame(
        ...    np.random.randn(50, 20),
        ...    columns=('col %d' % i for i in range(20)))
        ...
        >>> my_table._arrow_add_rows(df2)
        >>> # Now the table shown in the Streamlit app contains the data for
        >>> # df1 followed by the data for df2.

        You can do the same thing with plots. For example, if you want to add
        more data to a line chart:

        >>> # Assuming df1 and df2 from the example above still exist...
        >>> my_chart = st._arrow_line_chart(df1)
        >>> my_chart._arrow_add_rows(df2)
        >>> # Now the chart shown in the Streamlit app contains the data for
        >>> # df1 followed by the data for df2.

        And for plots whose datasets are named, you can pass the data with a
        keyword argument where the key is the name:

        >>> my_chart = st._arrow_vega_lite_chart({
        ...     'mark': 'line',
        ...     'encoding': {'x': 'a', 'y': 'b'},
        ...     'datasets': {
        ...       'some_fancy_name': df1,  # <-- named dataset
        ...      },
        ...     'data': {'name': 'some_fancy_name'},
        ... }),
        >>> my_chart._arrow_add_rows(some_fancy_name=df2)  # <-- name used as keyword

        """
        if self._root_container is None or self._cursor is None:
            return self

        if not self._cursor.is_locked:
            raise StreamlitAPIException("Only existing elements can `add_rows`.")

        # Accept syntax st._arrow_add_rows(df).
        if data is not None and len(kwargs) == 0:
            name = ""
        # Accept syntax st._arrow_add_rows(foo=df).
        elif len(kwargs) == 1:
            name, data = kwargs.popitem()
        # Raise error otherwise.
        else:
            raise StreamlitAPIException(
                "Wrong number of arguments to add_rows()."
                "Command requires exactly one dataset"
            )

        # When doing _arrow_add_rows on an element that does not already have data
        # (for example, st._arrow_line_chart() without any args), call the original
        # st._arrow_foo() element with new data instead of doing a _arrow_add_rows().
        if (
            self._cursor.props["delta_type"] in ARROW_DELTA_TYPES_THAT_MELT_DATAFRAMES
            and self._cursor.props["last_index"] is None
        ):
            # IMPORTANT: This assumes delta types and st method names always
            # match!
            # delta_type starts with "arrow_", but st_method_name starts with "_arrow_".
            st_method_name = "_" + self._cursor.props["delta_type"]
            st_method = getattr(self, st_method_name)
            st_method(data, **kwargs)
            return None

        data, self._cursor.props["last_index"] = _maybe_melt_data_for_add_rows(
            data, self._cursor.props["delta_type"], self._cursor.props["last_index"]
        )

        msg = ForwardMsg_pb2.ForwardMsg()
        msg.metadata.delta_path[:] = self._cursor.delta_path

        import streamlit.elements.arrow as arrow_proto

        default_uuid = str(hash(self._get_delta_path_str()))
        arrow_proto.marshall(msg.delta.arrow_add_rows.data, data, default_uuid)

        if name:
            msg.delta.arrow_add_rows.name = name
            msg.delta.arrow_add_rows.has_name = True

        _enqueue_message(msg)

        return self