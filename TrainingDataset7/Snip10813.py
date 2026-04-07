def _identity(cls, value):
        if isinstance(value, tuple):
            return tuple(map(cls._identity, value))
        if isinstance(value, dict):
            return tuple((key, cls._identity(val)) for key, val in value.items())
        if isinstance(value, fields.Field):
            if value.name and value.model:
                return value.model._meta.label, value.name
            return type(value)
        return make_hashable(value)