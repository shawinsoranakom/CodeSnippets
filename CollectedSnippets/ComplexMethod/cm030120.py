def _generic_class_getitem(cls, args):
    """Parameterizes a generic class.

    At least, parameterizing a generic class is the *main* thing this method
    does. For example, for some generic class `Foo`, this is called when we
    do `Foo[int]` - there, with `cls=Foo` and `args=int`.

    However, note that this method is also called when defining generic
    classes in the first place with `class Foo(Generic[T]): ...`.
    """
    if not isinstance(args, tuple):
        args = (args,)

    args = tuple(_type_convert(p) for p in args)
    is_generic_or_protocol = cls in (Generic, Protocol)

    if is_generic_or_protocol:
        # Generic and Protocol can only be subscripted with unique type variables.
        if not args:
            raise TypeError(
                f"Parameter list to {cls.__qualname__}[...] cannot be empty"
            )
        if not all(_is_typevar_like(p) for p in args):
            raise TypeError(
                f"Parameters to {cls.__name__}[...] must all be type variables "
                f"or parameter specification variables.")
        if len(set(args)) != len(args):
            raise TypeError(
                f"Parameters to {cls.__name__}[...] must all be unique")
    else:
        # Subscripting a regular Generic subclass.
        try:
            parameters = cls.__parameters__
        except AttributeError as e:
            init_subclass = getattr(cls, '__init_subclass__', None)
            if init_subclass not in {None, Generic.__init_subclass__}:
                e.add_note(
                    f"Note: this exception may have been caused by "
                    f"{init_subclass.__qualname__!r} (or the "
                    f"'__init_subclass__' method on a superclass) not "
                    f"calling 'super().__init_subclass__()'"
                )
            raise
        for param in parameters:
            prepare = getattr(param, '__typing_prepare_subst__', None)
            if prepare is not None:
                args = prepare(cls, args)
        _check_generic_specialization(cls, args)

        new_args = []
        for param, new_arg in zip(parameters, args):
            if isinstance(param, TypeVarTuple):
                new_args.extend(new_arg)
            else:
                new_args.append(new_arg)
        args = tuple(new_args)

    return _GenericAlias(cls, args)