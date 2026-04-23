def __getattr__(self, key: str) -> Any:
        """Return the value with the given key. If no such key
        exists, raise an AttributeError.

        Thread-safe.
        """
        try:
            value = self._parse(True)[key]
            if not isinstance(value, Mapping):
                return value
            else:
                return AttrDict(value)
        # We add FileNotFoundError since __getattr__ is expected to only raise
        # AttributeError. Without handling FileNotFoundError, unittests.mocks
        # fails during mock creation on Python3.9
        except (KeyError, FileNotFoundError):
            raise AttributeError(_missing_attr_error_message(key))