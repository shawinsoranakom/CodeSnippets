def __getitem__(self, i):
        error = self.data[i]
        if isinstance(error, ValidationError):
            return next(iter(error))
        return error