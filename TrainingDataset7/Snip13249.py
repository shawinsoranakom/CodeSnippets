def get(self, key, otherwise=None):
        return self.dicts[-1].get(key, otherwise)