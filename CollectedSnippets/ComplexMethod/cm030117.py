def evaluate_forward_ref(
    forward_ref,
    *,
    owner=None,
    globals=None,
    locals=None,
    type_params=None,
    format=None,
    _recursive_guard=frozenset(),
):
    """Evaluate a forward reference as a type hint.

    This is similar to calling the ForwardRef.evaluate() method,
    but unlike that method, evaluate_forward_ref() also
    recursively evaluates forward references nested within the type hint.

    *forward_ref* must be an instance of ForwardRef. *owner*, if given,
    should be the object that holds the annotations that the forward reference
    derived from, such as a module, class object, or function. It is used to
    infer the namespaces to use for looking up names. *globals* and *locals*
    can also be explicitly given to provide the global and local namespaces.
    *type_params* is a tuple of type parameters that are in scope when
    evaluating the forward reference. This parameter should be provided (though
    it may be an empty tuple) if *owner* is not given and the forward reference
    does not already have an owner set. *format* specifies the format of the
    annotation and is a member of the annotationlib.Format enum, defaulting to
    VALUE.

    """
    if format == _lazy_annotationlib.Format.STRING:
        return forward_ref.__forward_arg__
    if forward_ref.__forward_arg__ in _recursive_guard:
        return forward_ref

    if format is None:
        format = _lazy_annotationlib.Format.VALUE
    value = forward_ref.evaluate(globals=globals, locals=locals,
                                 type_params=type_params, owner=owner, format=format)

    if (isinstance(value, _lazy_annotationlib.ForwardRef)
            and format == _lazy_annotationlib.Format.FORWARDREF):
        return value

    if isinstance(value, str):
        value = _make_forward_ref(value, module=forward_ref.__forward_module__,
                                  owner=owner or forward_ref.__owner__,
                                  is_argument=forward_ref.__forward_is_argument__,
                                  is_class=forward_ref.__forward_is_class__)
    if owner is None:
        owner = forward_ref.__owner__
    return _eval_type(
        value,
        globals,
        locals,
        type_params,
        recursive_guard=_recursive_guard | {forward_ref.__forward_arg__},
        format=format,
        owner=owner,
        parent_fwdref=forward_ref,
    )