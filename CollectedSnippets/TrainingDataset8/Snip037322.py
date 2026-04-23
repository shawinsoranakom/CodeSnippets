def get_locked_cursor(self, **props) -> "LockedCursor":
        self._props = props
        return self