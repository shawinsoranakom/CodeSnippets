def _dp_init_subclass(sub_cls, *args, **kwargs) -> None:
    # Add function for datapipe instance to reinforce the type
    sub_cls.reinforce_type = reinforce_type

    # TODO:
    # - add global switch for type checking at compile-time

    # Ignore internal type class
    if getattr(sub_cls, "__type_class__", False):
        return

    # Check if the string type is valid
    if isinstance(sub_cls.type.param, ForwardRef):
        base_globals = sys.modules[sub_cls.__module__].__dict__
        try:
            param = _eval_type(sub_cls.type.param, base_globals, locals())
            sub_cls.type.param = param
        except TypeError as e:
            raise TypeError(
                f"{sub_cls.type.param.__forward_arg__} is not supported by Python typing"
            ) from e

    if "__iter__" in sub_cls.__dict__:
        iter_fn = sub_cls.__dict__["__iter__"]
        hints = get_type_hints(iter_fn)
        if "return" in hints:
            return_hint = hints["return"]
            # Plain Return Hint for Python 3.6
            if return_hint == Iterator:
                return
            if not (
                hasattr(return_hint, "__origin__")
                and (
                    return_hint.__origin__ == Iterator
                    or return_hint.__origin__ == collections.abc.Iterator
                )
            ):
                raise TypeError(
                    "Expected 'Iterator' as the return annotation for `__iter__` of {}"
                    ", but found {}".format(
                        sub_cls.__name__, _type_repr(hints["return"])
                    )
                )
            data_type = return_hint.__args__[0]
            if not issubtype(data_type, sub_cls.type.param):
                raise TypeError(
                    f"Expected return type of '__iter__' as a subtype of {sub_cls.type},"
                    f" but found {_type_repr(data_type)} for {sub_cls.__name__}"
                )