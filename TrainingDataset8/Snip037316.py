def get_locked_cursor(self, **props) -> "LockedCursor":
        locked_cursor = LockedCursor(
            root_container=self._root_container,
            parent_path=self._parent_path,
            index=self._index,
            **props,
        )

        self._index += 1

        return locked_cursor