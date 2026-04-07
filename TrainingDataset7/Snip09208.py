def make_cursor(self, cursor):
        """Create a cursor without debug logging."""
        return utils.CursorWrapper(cursor, self)