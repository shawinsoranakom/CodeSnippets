def close(self):
        try:
            self.cursor.close()
        except Database.InterfaceError:
            # already closed
            pass