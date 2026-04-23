def expander(self, label: str, expanded: bool = False) -> "DeltaGenerator":
        """Insert a multi-element container that can be expanded/collapsed.

        Inserts a container into your app that can be used to hold multiple elements
        and can be expanded or collapsed by the user. When collapsed, all that is
        visible is the provided label.

        To add elements to the returned container, you can use "with" notation
        (preferred) or just call methods directly on the returned object. See
        examples below.

        .. warning::
            Currently, you may not put expanders inside another expander.

        Parameters
        ----------
        label : str
            A string to use as the header for the expander. The label can optionally
            contain Markdown and supports the following elements: Bold, Italics,
            Strikethroughs, Inline Code, Emojis, and Links.
        expanded : bool
            If True, initializes the expander in "expanded" state. Defaults to
            False (collapsed).

        Examples
        --------

        You can use `with` notation to insert any element into an expander

        >>> st.bar_chart({"data": [1, 5, 2, 6, 2, 1]})
        >>>
        >>> with st.expander("See explanation"):
        ...     st.write(\"\"\"
        ...         The chart above shows some numbers I picked for you.
        ...         I rolled actual dice for these, so they're *guaranteed* to
        ...         be random.
        ...     \"\"\")
        ...     st.image("https://static.streamlit.io/examples/dice.jpg")

        .. output ::
            https://doc-expander.streamlitapp.com/
            height: 750px

        Or you can just call methods directly in the returned objects:

        >>> st.bar_chart({"data": [1, 5, 2, 6, 2, 1]})
        >>>
        >>> expander = st.expander("See explanation")
        >>> expander.write(\"\"\"
        ...     The chart above shows some numbers I picked for you.
        ...     I rolled actual dice for these, so they're *guaranteed* to
        ...     be random.
        ... \"\"\")
        >>> expander.image("https://static.streamlit.io/examples/dice.jpg")

        .. output ::
            https://doc-expander.streamlitapp.com/
            height: 750px

        """
        if label is None:
            raise StreamlitAPIException("A label is required for an expander")

        expandable_proto = BlockProto.Expandable()
        expandable_proto.expanded = expanded
        expandable_proto.label = label

        block_proto = BlockProto()
        block_proto.allow_empty = True
        block_proto.expandable.CopyFrom(expandable_proto)

        return self.dg._block(block_proto=block_proto)