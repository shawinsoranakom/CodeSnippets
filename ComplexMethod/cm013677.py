def _get_mod_type(
    fn: _score_mod_signature | _mask_mod_signature | Callable[..., Any],
) -> _ModificationType:
    """Get the type of modification function.
    This function inspects the number of positional arguments of the function to determine
    the type of modification function. If the function has 5 positional arguments, it is
    considered as a score_mod function. If the function has 4 positional arguments, it is
    considered as a mask function.
    """
    if hasattr(fn, "__code__"):
        code = fn.__code__
        num_positional_total = code.co_argcount
        defaults = ()
        if hasattr(fn, "__defaults__"):
            defaults = fn.__defaults__ or ()
        num_defaults = len(defaults)
        num_positional_args = num_positional_total - num_defaults
    else:
        num_positional_args = sum(
            1
            for param in inspect.signature(fn).parameters.values()
            if param.default is inspect.Parameter.empty
        )
    if num_positional_args != 5 and num_positional_args != 4:
        raise AssertionError(
            f"Expected 4 or 5 positional args, got {num_positional_args}"
        )
    if num_positional_args == 5:
        return _ModificationType.SCORE_MOD
    elif num_positional_args == 4:
        return _ModificationType.MASK_MOD
    else:
        return _ModificationType.UNKNOWN