def get(self, header, alternate=None):
        return self.headers.get(header, alternate)