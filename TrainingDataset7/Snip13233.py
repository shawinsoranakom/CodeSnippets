def __setitem__(self, key, value):
        "Set a variable in the current context"
        self.dicts[-1][key] = value