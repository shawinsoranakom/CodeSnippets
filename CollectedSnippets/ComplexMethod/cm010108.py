def handle_torch_function(
    public_api: Callable[_P, _R],
    relevant_args: Iterable[Any],
    *args: _P.args,
    **kwargs: _P.kwargs,
) -> _R:
    """Implement a function with checks for ``__torch_function__`` overrides.

    See torch::autograd::handle_torch_function for the equivalent of this
    function in the C++ implementation.

    Arguments
    ---------
    public_api : function
        Function exposed by the public torch API originally called like
        ``public_api(*args, **kwargs)`` on which arguments are now being
        checked.
    relevant_args : iterable
        Iterable of arguments to check for __torch_function__ methods.
    args : tuple
        Arbitrary positional arguments originally passed into ``public_api``.
    kwargs : tuple
        Arbitrary keyword arguments originally passed into ``public_api``.

    Returns
    -------
    object
        Result from calling ``implementation`` or an ``__torch_function__``
        method, as appropriate.

    Raises
    ------
    TypeError : if no implementation is found.

    Example
    -------
    >>> def func(a):
    ...     if has_torch_function_unary(a):
    ...         return handle_torch_function(func, (a,), a)
    ...     return a + 0
    """
    # Check for __torch_function__ methods.
    overloaded_args = _get_overloaded_args(relevant_args)
    # overloaded_args already have unique types.
    types = tuple(map(type, overloaded_args))

    # Check for __torch_function__ mode.
    if _is_torch_function_mode_enabled():
        # if we're here, the mode must be set to a TorchFunctionStackMode
        # this unsets it and calls directly into TorchFunctionStackMode's torch function
        with _pop_mode_temporarily() as mode:
            result = mode.__torch_function__(public_api, types, args, kwargs)
        if result is not NotImplemented:
            return result

    # Call overrides
    for overloaded_arg in overloaded_args:
        # This call needs to become a classmethod call in the future.
        # See https://github.com/pytorch/pytorch/issues/63767
        torch_func_method = overloaded_arg.__torch_function__
        if (
            hasattr(torch_func_method, "__self__")
            and torch_func_method.__self__ is overloaded_arg
            and torch_func_method is not torch._C._disabled_torch_function_impl
        ):
            warnings.warn(
                "Defining your `__torch_function__ as a plain method is deprecated and "
                "will be an error in future, please define it as a classmethod.",
                DeprecationWarning,
                stacklevel=2,
            )

        # Use `public_api` instead of `implementation` so __torch_function__
        # implementations can do equality/identity comparisons.
        result = torch_func_method(public_api, types, args, kwargs)

        if result is not NotImplemented:
            return result

    func_name = f"{public_api.__module__}.{public_api.__name__}"
    msg = (
        f"no implementation found for '{func_name}' on types that implement "
        f"__torch_function__: {[type(arg) for arg in overloaded_args]}"
    )
    if _is_torch_function_mode_enabled():
        msg += f" nor in mode {_get_current_function_mode()}"
    raise TypeError(msg)