def wrapped_func(*args, **kwargs):
        # Note: Since we use a wrapper, beta_ functions will not autocomplete
        # correctly on VSCode.
        result = func(*args, **kwargs)
        _show_beta_warning(func.__name__, date)
        return result