def __getattr__(self, item):
        return self.get(item)