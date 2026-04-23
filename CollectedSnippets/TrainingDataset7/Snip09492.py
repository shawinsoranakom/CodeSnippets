def create_cursor(self, name=None):
        cursor = self.connection.cursor()
        return CursorWrapper(cursor)