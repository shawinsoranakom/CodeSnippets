def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        if self.fillfactor is not None:
            kwargs["fillfactor"] = self.fillfactor
        return path, args, kwargs