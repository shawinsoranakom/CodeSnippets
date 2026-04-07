def deconstruct(self):
            name, path, args, kwargs = super().deconstruct()
            kwargs["default_bounds"] = "[)"
            return name, path, args, kwargs