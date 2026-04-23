def is_name_available(self, name, max_length=None):
        if self._allow_overwrite:
            return not (max_length and len(name) > max_length)
        return super().is_name_available(name, max_length=max_length)