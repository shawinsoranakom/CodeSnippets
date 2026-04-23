def wrap(fn_or_name: str | Callable[..., Any]) -> str | Callable[..., Any]:
    """
    This function can be called at module-level scope to register fn_or_name as a "leaf function".
    A "leaf function" will be preserved as a CallFunction node in the FX trace instead of being
    traced through::

        # foo/bar/baz.py
        def my_custom_function(x, y):
            return x * x + y * y


        torch.fx.wrap("my_custom_function")


        def fn_to_be_traced(x, y):
            # When symbolic tracing, the below call to my_custom_function will be inserted into
            # the graph rather than tracing it.
            return my_custom_function(x, y)

    This function can also equivalently be used as a decorator::

        # foo/bar/baz.py
        @torch.fx.wrap
        def my_custom_function(x, y):
            return x * x + y * y

    A wrapped function can be thought of a "leaf function", analogous to the concept of
    "leaf modules", that is, they are functions that are left as calls in the FX trace
    rather than traced through.

    Args:

        fn_or_name (Union[str, Callable]): The function or name of the global function to insert into the
            graph when it's called
    """
    if not callable(fn_or_name) and not isinstance(fn_or_name, str):
        raise RuntimeError(
            "Unsupported type for global function! Must be either a callable or "
            "string name"
        )

    if callable(fn_or_name):
        if isinstance(fn_or_name, str):  # to make mypy happy
            raise AssertionError("Unexpected: fn_or_name is both callable and str")
        fn_name = fn_or_name.__name__
    else:
        if not isinstance(fn_or_name, str):
            raise AssertionError(
                f"fn_or_name must be a global function or string name, got "
                f"{type(fn_or_name)}"
            )
        fn_name = fn_or_name

    currentframe = inspect.currentframe()
    if currentframe is None:
        raise AssertionError("inspect.currentframe() returned None")
    f = currentframe.f_back
    if f is None:
        raise AssertionError("currentframe.f_back is None")
    if f.f_code.co_name != "<module>":
        raise NotImplementedError("wrap must be called at the top level of a module")

    # consider implementing Callable version of this via _autowrap_function_ids / _autowrap_search
    # semantics would be slightly different, but would add support `from x import wrapped_function`
    _wrapped_fns_to_patch[(id(f.f_globals), fn_name)] = f.f_globals
    return fn_or_name