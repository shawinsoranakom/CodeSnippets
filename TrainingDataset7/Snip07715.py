def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.default_bounds and self.default_bounds != CANONICAL_RANGE_BOUNDS:
            kwargs["default_bounds"] = self.default_bounds
        return name, path, args, kwargs