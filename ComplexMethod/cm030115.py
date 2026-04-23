def _collect_type_parameters(
    args,
    *,
    enforce_default_ordering: bool = True,
    validate_all: bool = False,
):
    """Collect all type parameters in args
    in order of first appearance (lexicographic order).

    Having an explicit `Generic` or `Protocol` base class determines
    the exact parameter order.

    For example::

        >>> P = ParamSpec('P')
        >>> T = TypeVar('T')
        >>> _collect_type_parameters((T, Callable[P, T]))
        (~T, ~P)
        >>> _collect_type_parameters((list[T], Generic[P, T]))
        (~P, ~T)

    """
    # required type parameter cannot appear after parameter with default
    default_encountered = False
    # or after TypeVarTuple
    type_var_tuple_encountered = False
    parameters = []
    for t in args:
        if isinstance(t, type):
            # We don't want __parameters__ descriptor of a bare Python class.
            pass
        elif isinstance(t, tuple):
            # `t` might be a tuple, when `ParamSpec` is substituted with
            # `[T, int]`, or `[int, *Ts]`, etc.
            for x in t:
                for collected in _collect_type_parameters([x]):
                    if collected not in parameters:
                        parameters.append(collected)
        elif hasattr(t, '__typing_subst__'):
            if t not in parameters:
                if enforce_default_ordering:
                    if type_var_tuple_encountered and t.has_default():
                        raise TypeError('Type parameter with a default'
                                        ' follows TypeVarTuple')

                    if t.has_default():
                        default_encountered = True
                    elif default_encountered:
                        raise TypeError(f'Type parameter {t!r} without a default'
                                        ' follows type parameter with a default')

                parameters.append(t)
        elif (
            not validate_all
            and isinstance(t, _GenericAlias)
            and t.__origin__ in (Generic, Protocol)
        ):
            # If we see explicit `Generic[...]` or `Protocol[...]` base classes,
            # we need to just copy them as-is.
            # Unless `validate_all` is passed, in this case it means that
            # we are doing a validation of `Generic` subclasses,
            # then we collect all unique parameters to be able to inspect them.
            parameters = t.__parameters__
        else:
            if _is_unpacked_typevartuple(t):
                type_var_tuple_encountered = True
            for x in getattr(t, '__parameters__', ()):
                if x not in parameters:
                    parameters.append(x)
    return tuple(parameters)