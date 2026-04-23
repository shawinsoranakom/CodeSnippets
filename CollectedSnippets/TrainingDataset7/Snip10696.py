def deconstruct(self):
        path, args, kwargs = super().deconstruct()
        kwargs["condition"] = self.condition
        return path, args, kwargs