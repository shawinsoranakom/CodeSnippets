def from_param(cls, context, param):
        if param is None:
            return None
        if isinstance(param, (list, tuple)):
            if not param:
                return None
            return cls(*param)
        elif isinstance(param, str) or hasattr(param, "resolve_expression"):
            return cls(param)
        raise ValueError(
            f"{context} must be either a string reference to a "
            f"field, an expression, or a list or tuple of them not {param!r}."
        )