def method_has_no_args(meth):
    """Return True if a method only accepts 'self'."""
    count = len([p for p in _get_callable_parameters(meth) if p.kind in ARG_KINDS])
    return count == 0 if inspect.ismethod(meth) else count == 1