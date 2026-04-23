def __missing__(self, key):
        self[key] = self.word.count(key)
        return self[key]