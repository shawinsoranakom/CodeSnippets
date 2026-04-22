def columns(
        self, spec: SpecType, *, gap: Optional[str] = "small"
    ) -> List["DeltaGenerator"]:
        """Insert containers laid out as side-by-side columns.

        Inserts a number of multi-element containers laid out side-by-side and
        returns a list of container objects.

        To add elements to the returned containers, you can use "with" notation
        (preferred) or just call methods directly on the returned object. See
        examples below.

        .. warning::
            Currently, you may not put columns inside another column.

        Parameters
        ----------
        spec : int or list of numbers
            If an int
                Specifies the number of columns to insert, and all columns
                have equal width.

            If a list of numbers
                Creates a column for each number, and each
                column's width is proportional to the number provided. Numbers can
                be ints or floats, but they must be positive.

                For example, `st.columns([3, 1, 2])` creates 3 columns where
                the first column is 3 times the width of the second, and the last
                column is 2 times that width.
        gap : string ("small", "medium", or "large")
            An optional string, which indicates the size of the gap between each column.
            The default is a small gap between columns. This argument can only be supplied by
            keyword.

        Returns
        -------
        list of containers
            A list of container objects.

        Examples
        --------

        You can use `with` notation to insert any element into a column:

        >>> col1, col2, col3 = st.columns(3)
        >>>
        >>> with col1:
        ...    st.header("A cat")
        ...    st.image("https://static.streamlit.io/examples/cat.jpg")
        ...
        >>> with col2:
        ...    st.header("A dog")
        ...    st.image("https://static.streamlit.io/examples/dog.jpg")
        ...
        >>> with col3:
        ...    st.header("An owl")
        ...    st.image("https://static.streamlit.io/examples/owl.jpg")

        .. output ::
            https://doc-columns1.streamlitapp.com/
            height: 620px

        Or you can just call methods directly in the returned objects:

        >>> col1, col2 = st.columns([3, 1])
        >>> data = np.random.randn(10, 1)
        >>>
        >>> col1.subheader("A wide column with a chart")
        >>> col1.line_chart(data)
        >>>
        >>> col2.subheader("A narrow column with the data")
        >>> col2.write(data)

        .. output ::
            https://doc-columns2.streamlitapp.com/
            height: 550px

        """
        weights = spec
        weights_exception = StreamlitAPIException(
            "The input argument to st.columns must be either a "
            + "positive integer or a list of positive numeric weights. "
            + "See [documentation](https://docs.streamlit.io/library/api-reference/layout/st.columns) "
            + "for more information."
        )

        if isinstance(weights, int):
            # If the user provided a single number, expand into equal weights.
            # E.g. (1,) * 3 => (1, 1, 1)
            # NOTE: A negative/zero spec will expand into an empty tuple.
            weights = (1,) * weights

        if len(weights) == 0 or any(weight <= 0 for weight in weights):
            raise weights_exception

        def column_gap(gap):
            if type(gap) == str:
                gap_size = gap.lower()
                valid_sizes = ["small", "medium", "large"]

                if gap_size in valid_sizes:
                    return gap_size

            raise StreamlitAPIException(
                'The gap argument to st.columns must be "small", "medium", or "large". \n'
                f"The argument passed was {gap}."
            )

        gap_size = column_gap(gap)

        def column_proto(normalized_weight: float) -> BlockProto:
            col_proto = BlockProto()
            col_proto.column.weight = normalized_weight
            col_proto.column.gap = gap_size
            col_proto.allow_empty = True
            return col_proto

        block_proto = BlockProto()
        block_proto.horizontal.gap = gap_size
        row = self.dg._block(block_proto)
        total_weight = sum(weights)
        return [row._block(column_proto(w / total_weight)) for w in weights]