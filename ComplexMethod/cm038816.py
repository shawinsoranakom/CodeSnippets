def supports_kw(
    callable: Callable[..., object],
    kw_name: str,
    *,
    requires_kw_only: bool = False,
    allow_var_kwargs: bool = True,
) -> bool:
    """Check if a keyword is a valid kwarg for a callable; if requires_kw_only
    disallows kwargs names that can also be positional arguments.
    """
    params = inspect.signature(callable).parameters
    if not params:
        return False

    param_val = params.get(kw_name)

    # Types where the it may be valid, i.e., explicitly defined & nonvariadic
    passable_kw_types = set(
        (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        )
    )

    if param_val:
        is_sig_param = param_val.kind in passable_kw_types
        # We want kwargs only, but this is passable as a positional arg
        if (
            requires_kw_only
            and is_sig_param
            and param_val.kind != inspect.Parameter.KEYWORD_ONLY
        ):
            return False
        if (requires_kw_only and param_val.kind == inspect.Parameter.KEYWORD_ONLY) or (
            not requires_kw_only and is_sig_param
        ):
            return True

    # If we're okay with var-kwargs, it's supported as long as
    # the kw_name isn't something like *args, **kwargs
    if allow_var_kwargs:
        # Get the last param; type is ignored here because params is a proxy
        # mapping, but it wraps an ordered dict, and they appear in order.
        # Ref: https://docs.python.org/3/library/inspect.html#inspect.Signature.parameters
        last_param = params[next(reversed(params))]  # type: ignore
        return (
            last_param.kind == inspect.Parameter.VAR_KEYWORD
            and last_param.name != kw_name
        )

    return False