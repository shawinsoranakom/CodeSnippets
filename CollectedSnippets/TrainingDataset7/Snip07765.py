def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        if self.length is not None:
            kwargs["length"] = self.length
        if self.columns:
            kwargs["columns"] = self.columns
        return path, args, kwargs