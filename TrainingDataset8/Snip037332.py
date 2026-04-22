def __init__(
        self,
        root_container: Optional[int] = RootContainer.MAIN,
        cursor: Optional[Cursor] = None,
        parent: Optional["DeltaGenerator"] = None,
        block_type: Optional[str] = None,
    ) -> None:
        """Inserts or updates elements in Streamlit apps.

        As a user, you should never initialize this object by hand. Instead,
        DeltaGenerator objects are initialized for you in two places:

        1) When you call `dg = st.foo()` for some method "foo", sometimes `dg`
        is a DeltaGenerator object. You can call methods on the `dg` object to
        update the element `foo` that appears in the Streamlit app.

        2) This is an internal detail, but `st.sidebar` itself is a
        DeltaGenerator. That's why you can call `st.sidebar.foo()` to place
        an element `foo` inside the sidebar.

        """
        # Sanity check our Container + Cursor, to ensure that our Cursor
        # is using the same Container that we are.
        if (
            root_container is not None
            and cursor is not None
            and root_container != cursor.root_container
        ):
            raise RuntimeError(
                "DeltaGenerator root_container and cursor.root_container must be the same"
            )

        # Whether this DeltaGenerator is nested in the main area or sidebar.
        # No relation to `st.container()`.
        self._root_container = root_container

        # NOTE: You should never use this directly! Instead, use self._cursor,
        # which is a computed property that fetches the right cursor.
        self._provided_cursor = cursor

        self._parent = parent
        self._block_type = block_type

        # If this an `st.form` block, this will get filled in.
        self._form_data: Optional[FormData] = None

        # Change the module of all mixin'ed functions to be st.delta_generator,
        # instead of the original module (e.g. st.elements.markdown)
        for mixin in self.__class__.__bases__:
            for (name, func) in mixin.__dict__.items():
                if callable(func):
                    func.__module__ = self.__module__