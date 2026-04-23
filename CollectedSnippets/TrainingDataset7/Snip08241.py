def get(self, key, default=None, version=None):
        return self.get_many([key], version).get(key, default)