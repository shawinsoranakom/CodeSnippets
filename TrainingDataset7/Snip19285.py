def rowcount(self):
                if self.is_closed:
                    raise Exception("Cursor is closed.")
                return self.cursor.rowcount