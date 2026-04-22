def container(self) -> "DeltaGenerator":
        """Insert a multi-element container.

        Inserts an invisible container into your app that can be used to hold
        multiple elements. This allows you to, for example, insert multiple
        elements into your app out of order.

        To add elements to the returned container, you can use "with" notation
        (preferred) or just call methods directly on the returned object. See
        examples below.

        Examples
        --------

        Inserting elements using "with" notation:

        >>> with st.container():
        ...    st.write("This is inside the container")
        ...
        ...    # You can call any Streamlit command, including custom components:
        ...    st.bar_chart(np.random.randn(50, 3))
        ...
        >>> st.write("This is outside the container")

        .. output ::
            https://doc-container1.streamlitapp.com/
            height: 520px

        Inserting elements out of order:

        >>> container = st.container()
        >>> container.write("This is inside the container")
        >>> st.write("This is outside the container")
        >>>
        >>> # Now insert some more in the container
        >>> container.write("This is inside too")

        .. output ::
            https://doc-container2.streamlitapp.com/
            height: 480px
        """
        return self.dg._block()