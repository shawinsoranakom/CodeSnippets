def __getitem__(self, key: str) -> Any:
        try:
            value = self.__nested_secrets__[key]
            return self._maybe_wrap_in_attr_dict(value)
        except KeyError:
            raise KeyError(_missing_key_error_message(key))