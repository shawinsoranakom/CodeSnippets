def __call__(self, *args, **kwargs):
        if self.key == "lookupfunc":
            return SQLFuncLookup(self.name, *args, **kwargs)
        return SQLFuncTransform(self.name, *args, **kwargs)