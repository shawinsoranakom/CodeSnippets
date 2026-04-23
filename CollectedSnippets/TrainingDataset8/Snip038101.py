def __getitem__(self, key: str) -> Any:
        """Return the value with the given key. If no such key
        exists, raise a KeyError.

        Thread-safe.
        """
        try:
            value = self._parse(True)[key]
            if not isinstance(value, Mapping):
                return value
            else:
                return AttrDict(value)
        except KeyError:
            raise KeyError(_missing_key_error_message(key))