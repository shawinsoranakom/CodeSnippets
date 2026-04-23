def has_changed(k, v):
        if k not in init_params:  # happens if k is part of a **kwargs
            return True
        if init_params[k] == inspect._empty:  # k has no default value
            return True
        # try to avoid calling repr on nested estimators
        if isinstance(v, BaseEstimator) and v.__class__ != init_params[k].__class__:
            return True
        # Use repr as a last resort. It may be expensive.
        if repr(v) != repr(init_params[k]) and not (
            is_scalar_nan(init_params[k]) and is_scalar_nan(v)
        ):
            return True
        return False