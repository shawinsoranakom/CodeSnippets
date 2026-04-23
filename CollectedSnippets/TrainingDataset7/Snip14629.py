def read(self):
        ret = self.getvalue()
        self.seek(0)
        self.truncate()
        return ret