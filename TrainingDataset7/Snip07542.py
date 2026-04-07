def check_unique(self, unique):
        "Check the `unique` keyword parameter -- may be a sequence or string."
        if isinstance(unique, (list, tuple)):
            # List of fields to determine uniqueness with
            for attr in unique:
                if attr not in self.mapping:
                    raise ValueError
        elif isinstance(unique, str):
            # Only a single field passed in.
            if unique not in self.mapping:
                raise ValueError
        else:
            raise TypeError(
                "Unique keyword argument must be set with a tuple, list, or string."
            )