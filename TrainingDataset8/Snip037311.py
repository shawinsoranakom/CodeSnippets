def __init__(self, root_container: int, parent_path: Tuple[int, ...] = ()):
        """A moving pointer to a delta location in the app.

        RunningCursors auto-increment to the next available location when you
        call get_locked_cursor() on them.

        Parameters
        ----------
        root_container: int
            The root container this cursor lives in.
        parent_path: tuple of ints
          The full path of this cursor, consisting of the IDs of all ancestors.
          The 0th item is the topmost ancestor.

        """
        self._root_container = root_container
        self._parent_path = parent_path
        self._index = 0