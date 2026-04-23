def _convert_out_params(f):
    out_annotation = f.__annotations__.get("out")

    # If there are no out params, do not wrap the function.
    if not out_annotation:
        return f

    # Hack to detect when out is a Tuple. There seems to be no pretty way of doing this
    if getattr(out_annotation, "__origin__", None) is tuple:
        sig = inspect.signature(f)
        out_names = sig.return_annotation._fields
        # If out is a tuple, we need to register a function that unpacks all the out
        # elements as this is what native_functions.yaml expects

        @wraps(f)
        def _fn(*args, **kwargs):
            out_kwargs = tuple(kwargs.pop(o, None) for o in out_names)
            # Either all of the out kwargs are set or none of them
            is_none = out_kwargs[0] is None
            if not all((o is None) == is_none for o in out_kwargs):
                raise AssertionError(
                    f"all out kwargs must be set or none of them, got {out_kwargs}"
                )
            return f(*args, **kwargs, out=None if is_none else out_kwargs)

        out_params = [
            inspect.Parameter(
                o,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=t,
            )
            for o, t in zip(out_names, out_annotation.__args__)
        ]
        # Drop the out parameter and concatenate the new kwargs in the signature
        params = chain((v for k, v in sig.parameters.items() if k != "out"), out_params)
        _fn.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
            parameters=params,  # type: ignore[arg-type]
            return_annotation=sig.return_annotation,
        )
        # Drop the out parameter and concatenate the new kwargs in the annotations
        _fn.__annotations__ = {k: v for k, v in f.__annotations__.items() if k != "out"}
        for o in out_params:
            _fn.__annotations__[o.name] = o.annotation

        # Propagate that this function is wrapped by `out_wrapper`
        _fn._torch_decompositions_out_wrapper = f._torch_decompositions_out_wrapper  # type: ignore[attr-defined]

        return _fn

    # Alternatively, there may be a single tensor out parameter with a name
    # other than "out". This will need special treatment and is indicated by an
    # annotation, which we will remove here so it is not exposed after wrapping.
    custom_out_param_name = f.__annotations__.pop(CustomOutParamAnnotation, None)
    if custom_out_param_name:

        @wraps(f)
        def _fn(*args, **kwargs):
            out_kwarg = kwargs.pop(custom_out_param_name, None)
            return f(*args, **kwargs, out=out_kwarg)

        out_param = inspect.Parameter(
            custom_out_param_name,
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=None,
            annotation=out_annotation,
        )

        # Drop the out parameter and concatenate the new kwarg in the signature
        sig = inspect.signature(f)
        params = chain(
            (v for k, v in sig.parameters.items() if k != "out"), (out_param,)
        )
        _fn.__signature__ = inspect.Signature(  # type: ignore[attr-defined]
            parameters=params,  # type: ignore[arg-type]
            return_annotation=sig.return_annotation,
        )

        # Drop the out parameter and concatenate the new kwargs in the annotations
        _fn.__annotations__ = {k: v for k, v in f.__annotations__.items() if k != "out"}
        _fn.__annotations__[out_param.name] = out_param.annotation

        return _fn

    return f