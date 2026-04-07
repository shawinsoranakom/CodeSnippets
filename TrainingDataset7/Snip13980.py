def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default