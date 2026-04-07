def make_debug_cursor(self, cursor):
        """Create a cursor that logs all queries in self.queries_log."""
        return utils.CursorDebugWrapper(cursor, self)