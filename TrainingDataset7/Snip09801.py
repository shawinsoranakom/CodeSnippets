def make_debug_cursor(self, cursor):
        return CursorDebugWrapper(cursor, self)