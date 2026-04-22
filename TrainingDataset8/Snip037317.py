def __init__(
        self,
        root_container: int,
        parent_path: Tuple[int, ...] = (),
        index: int = 0,
        **props,
    ):
        """A locked pointer to a location in the app.

        LockedCursors always point to the same location, even when you call
        get_locked_cursor() on them.

        Parameters
        ----------
        root_container: int
            The root container this cursor lives in.
        parent_path: tuple of ints
          The full path of this cursor, consisting of the IDs of all ancestors. The
          0th item is the topmost ancestor.
        index: int
        **props: any
          Anything else you want to store in this cursor. This is a temporary
          measure that will go away when we implement improved return values
          for elements.

        """
        self._root_container = root_container
        self._index = index
        self._parent_path = parent_path
        self._props = props