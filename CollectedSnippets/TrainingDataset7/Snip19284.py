def close(self):
                self.cursor.close()
                self.is_closed = True