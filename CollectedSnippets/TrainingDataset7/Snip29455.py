def deconstruct(self):
            name, path, args, kwargs = super().deconstruct()
            kwargs.update(
                {
                    "base_field": "",
                    "size": 1,
                }
            )
            return name, path, args, kwargs