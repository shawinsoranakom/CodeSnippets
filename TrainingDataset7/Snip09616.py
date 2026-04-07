def create_cursor(self, name=None):
        return FormatStylePlaceholderCursor(self.connection, self)