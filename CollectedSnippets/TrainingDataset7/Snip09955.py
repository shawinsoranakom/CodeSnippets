def create_cursor(self, name=None):
        return self.connection.cursor(factory=SQLiteCursorWrapper)