def transform_args(
    args: list[Any],
    kwargs: dict[str, Any],
    broadcast: bool,
    type_promotion_kind: ELEMENTWISE_TYPE_PROMOTION_KIND | None,
    convert_input_to_bool: bool,
) -> tuple[list[Any], dict[str, Any]]:
    """
    Transforms arguments for broadcasting and type promotion
    """

    args_indices = [i for i, x in enumerate(args) if isinstance(x, TensorBox)]
    kwargs_indices = [k for k, v in kwargs.items() if isinstance(v, TensorBox)]
    # check that there's something to transform
    if not args_indices and not kwargs_indices:
        return args, kwargs

    if type_promotion_kind or convert_input_to_bool:
        if convert_input_to_bool:
            dtype = torch.bool
        else:
            # FIXME this is a crude approximation for promoting args
            promoting_args = [
                a
                for a in args
                if isinstance(a, (Number, sympy.Basic)) or hasattr(a, "dtype")
            ]
            # only consider tensor kwargs for promotion, for now
            promoting_args.extend(a for a in kwargs.values() if hasattr(a, "dtype"))
            dtype = get_promoted_dtype(
                *promoting_args,
                type_promotion_kind=type_promotion_kind,  # type: ignore[arg-type]
            )

        device = (
            args[args_indices[0]] if args_indices else kwargs[kwargs_indices[0]]
        ).get_device()

        for i in args_indices:
            args[i] = maybe_copy_cpu_scalar(args[i], device)

        for k in kwargs_indices:
            kwargs[k] = maybe_copy_cpu_scalar(kwargs[k], device)

        # sometimes args are an immutable list so we can't mutate them
        def promote(arg: Any) -> Any:
            if isinstance(arg, TensorBox):
                return to_dtype(arg, dtype)
            elif isinstance(arg, ir.Constant):
                return ir.Constant(value=arg.value, dtype=dtype, device=device)
            else:
                return arg

        args = [promote(a) for a in args]
        kwargs = {k: promote(v) for k, v in kwargs.items()}

    if broadcast:
        broadcasted = broadcast_tensors(
            *list(
                itertools.chain(
                    (args[i] for i in args_indices),
                    (kwargs[k] for k in kwargs_indices),
                )
            )
        )
        size = list(broadcasted[0].get_size())

        for i, x in zip(args_indices, broadcasted[: len(args_indices)]):
            args[i] = x
        for k, x in zip(kwargs_indices, broadcasted[len(args_indices) :]):
            kwargs[k] = x

        for i in range(len(args)):
            if isinstance(args[i], ir.Constant):
                args[i] = ExpandView.create(args[i], size)
        for k in kwargs:
            if isinstance(kwargs[k], ir.Constant):
                kwargs[k] = ExpandView.create(kwargs[k], size)

    return args, kwargs