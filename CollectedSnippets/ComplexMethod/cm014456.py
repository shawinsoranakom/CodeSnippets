def _check_unpickable_fn(fn: Callable) -> None:
    """
    Check function is pickable or not.

    If it is a lambda or local function, a UserWarning will be raised. If it's not a callable function, a TypeError will be raised.
    """
    if not callable(fn):
        raise TypeError(f"A callable function is expected, but {type(fn)} is provided.")

    # Extract function from partial object
    # Nested partial function is automatically expanded as a single partial object
    if isinstance(fn, functools.partial):
        fn = fn.func

    # Local function
    if _is_local_fn(fn) and not dill_available():
        warnings.warn(
            "Local function is not supported by pickle, please use "
            "regular python function or functools.partial instead.",
            stacklevel=2,
        )
        return

    # Lambda function
    if hasattr(fn, "__name__") and fn.__name__ == "<lambda>" and not dill_available():
        warnings.warn(
            "Lambda function is not supported by pickle, please use "
            "regular python function or functools.partial instead.",
            stacklevel=2,
        )
        return