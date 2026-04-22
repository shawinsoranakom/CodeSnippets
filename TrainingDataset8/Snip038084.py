def _maybe_wrap_in_attr_dict(value) -> Any:
        if not isinstance(value, Mapping):
            return value
        else:
            return AttrDict(value)