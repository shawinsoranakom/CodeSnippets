def __getattr__(self, attr):
        return getattr(self.cursor, attr)