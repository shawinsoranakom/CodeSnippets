def __getattr__(self, attr_name: str) -> Any:
        try:
            value = self.__nested_secrets__[attr_name]
            return self._maybe_wrap_in_attr_dict(value)
        except KeyError:
            raise AttributeError(_missing_attr_error_message(attr_name))