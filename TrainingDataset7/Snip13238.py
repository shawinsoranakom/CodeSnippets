def get(self, key, otherwise=None):
        for d in reversed(self.dicts):
            if key in d:
                return d[key]
        return otherwise