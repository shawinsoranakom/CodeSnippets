def __getitem__(self, key):
        if isinstance(key, str):
            for subcontext in self:
                if key in subcontext:
                    return subcontext[key]
            raise KeyError(key)
        else:
            return super().__getitem__(key)