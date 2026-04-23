def tabs(self, tabs: Sequence[str]) -> Sequence["DeltaGenerator"]:
        """Insert containers separated into tabs.

        Inserts a number of multi-element containers as tabs.
        Tabs are a navigational element that allows users to easily
        move between groups of related content.

        To add elements to the returned containers, you can use "with" notation
        (preferred) or just call methods directly on the returned object. See
        examples below.

        .. warning::
            All the content of every tab is always sent to and rendered on the frontend.
            Conditional rendering is currently not supported.

        Parameters
        ----------
        tabs : list of strings
            Creates a tab for each string in the list. The first tab is selected by default.
            The string is used as the name of the tab and can optionally contain Markdown,
            supporting the following elements: Bold, Italics, Strikethroughs, Inline Code,
            Emojis, and Links.


        Returns
        -------
        list of containers
            A list of container objects.

        Examples
        --------

        You can use `with` notation to insert any element into a tab:

        >>> tab1, tab2, tab3 = st.tabs(["Cat", "Dog", "Owl"])
        >>>
        >>> with tab1:
        ...    st.header("A cat")
        ...    st.image("https://static.streamlit.io/examples/cat.jpg", width=200)
        ...
        >>> with tab2:
        ...    st.header("A dog")
        ...    st.image("https://static.streamlit.io/examples/dog.jpg", width=200)
        ...
        >>> with tab3:
        ...    st.header("An owl")
        ...    st.image("https://static.streamlit.io/examples/owl.jpg", width=200)

        .. output ::
            https://doc-tabs1.streamlitapp.com/
            height: 620px

        Or you can just call methods directly in the returned objects:

        >>> tab1, tab2 = st.tabs(["📈 Chart", "🗃 Data"])
        >>> data = np.random.randn(10, 1)
        >>>
        >>> tab1.subheader("A tab with a chart")
        >>> tab1.line_chart(data)
        >>>
        >>> tab2.subheader("A tab with the data")
        >>> tab2.write(data)


        .. output ::
            https://doc-tabs2.streamlitapp.com/
            height: 700px

        """
        if not tabs:
            raise StreamlitAPIException(
                "The input argument to st.tabs must contain at least one tab label."
            )

        if any(isinstance(tab, str) == False for tab in tabs):
            raise StreamlitAPIException(
                "The tabs input list to st.tabs is only allowed to contain strings."
            )

        def tab_proto(label: str) -> BlockProto:
            tab_proto = BlockProto()
            tab_proto.tab.label = label
            tab_proto.allow_empty = True
            return tab_proto

        block_proto = BlockProto()
        block_proto.tab_container.SetInParent()
        tab_container = self.dg._block(block_proto)
        return tuple(tab_container._block(tab_proto(tab_label)) for tab_label in tabs)