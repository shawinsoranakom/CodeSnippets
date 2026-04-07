def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["expressions"] = self.expressions
        if self.condition is not None:
            kwargs["condition"] = self.condition
        if self.index_type.lower() != "gist":
            kwargs["index_type"] = self.index_type
        if self.deferrable:
            kwargs["deferrable"] = self.deferrable
        if self.include:
            kwargs["include"] = self.include
        return path, args, kwargs