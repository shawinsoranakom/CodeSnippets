def _check_allowed(self, items):
        if hasattr(self, "_allowed"):
            if False in [isinstance(val, self._allowed) for val in items]:
                raise TypeError("Invalid type encountered in the arguments.")