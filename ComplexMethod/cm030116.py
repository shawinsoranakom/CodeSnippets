def _eval_type(t, globalns, localns, type_params, *, recursive_guard=frozenset(),
               format=None, owner=None, parent_fwdref=None, prefer_fwd_module=False):
    """Evaluate all forward references in the given type t.

    For use of globalns and localns see the docstring for get_type_hints().
    recursive_guard is used to prevent infinite recursion with a recursive
    ForwardRef.
    """
    if isinstance(t, _lazy_annotationlib.ForwardRef):
        # If the forward_ref has __forward_module__ set, evaluate() infers the globals
        # from the module, and it will probably pick better than the globals we have here.
        # We do this only for calls from get_type_hints() (which opts in through the
        # prefer_fwd_module flag), so that the default behavior remains more straightforward.
        if prefer_fwd_module and t.__forward_module__ is not None:
            globalns = None
            # If there are type params on the owner, we need to add them back, because
            # annotationlib won't.
            if owner_type_params := getattr(owner, "__type_params__", None):
                globalns = getattr(
                    sys.modules.get(t.__forward_module__, None), "__dict__", None
                )
                if globalns is not None:
                    globalns = dict(globalns)
                    for type_param in owner_type_params:
                        globalns[type_param.__name__] = type_param
        return evaluate_forward_ref(t, globals=globalns, locals=localns,
                                    type_params=type_params, owner=owner,
                                    _recursive_guard=recursive_guard, format=format)
    if isinstance(t, (_GenericAlias, GenericAlias, Union)):
        if isinstance(t, GenericAlias):
            args = tuple(
                _make_forward_ref(arg, parent_fwdref=parent_fwdref) if isinstance(arg, str) else arg
                for arg in t.__args__
            )
        else:
            args = t.__args__

        ev_args = tuple(
            _eval_type(
                a, globalns, localns, type_params, recursive_guard=recursive_guard,
                format=format, owner=owner, prefer_fwd_module=prefer_fwd_module,
            )
            for a in args
        )
        if ev_args == t.__args__:
            return t
        if isinstance(t, GenericAlias):
            return _rebuild_generic_alias(t, ev_args)
        if isinstance(t, Union):
            return functools.reduce(operator.or_, ev_args)
        else:
            return t.copy_with(ev_args)
    return t