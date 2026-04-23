def do_auto_functionalize(
    mode: "torch._subclasses.functional_tensor.FunctionalTensorMode",
    op: OpOverload,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> Any:
    """Functionalizes a call to op(*args, **kwargs) by emitting a call to
    `outs = auto_functionalized(op, normalized_kwargs)`
    and replacing the mutated (args, kwargs) with the corresponding outputs.

    The normalized_kwargs are just the (args, kwargs), but all in kwarg form.
    This makes handling easier for the auto_functionalized HOP.
    """
    from torch._subclasses.functional_tensor import PythonFunctionalizeAPI

    ctx = PythonFunctionalizeAPI(mode=mode)

    # All of the (args, kwargs), but all as kwargs. The names for the
    # args come from the schema. This makes it easier for us to work with them.
    normalized_kwargs = {}
    schema = op._schema
    for idx, arg in enumerate(schema.arguments):
        # NB: torch_dispatch kwargs are the args defined as kwarg-only in the schema
        if arg.name in kwargs:
            normalized_kwargs[arg.name] = kwargs[arg.name]
        elif idx < len(args):
            # if its out of bounds we don't need to do anything
            # as it means the optional arg was passed with its default
            # value
            normalized_kwargs[arg.name] = args[idx]
        else:
            normalized_kwargs[arg.name] = arg.default_value

    unwrapped_kwargs = ctx.unwrap_tensors(normalized_kwargs)  # type: ignore[arg-type]
    if "self" in unwrapped_kwargs or "self_" in unwrapped_kwargs:
        warnings.warn(
            "Using `self` or `self_` as an argument in the definition of custom ops may lead to ambiguous parsing. "
            "Please consider using a different name for this argument to avoid potential issues.",
            stacklevel=2,
        )
    with ctx.redispatch_to_next():
        unwrapped_outs = auto_functionalized(
            op,
            **unwrapped_kwargs,  # type: ignore[arg-type]
        )

    # List of the name of args that get mutated (according to the schema)
    mutable_args_names, _ = get_mutable_args(op)

    unwrapped_actual_out: Any | tuple[Any] = unwrapped_outs[: -len(mutable_args_names)]
    unwrapped_mutable_out = unwrapped_outs[-len(mutable_args_names) :]

    if len(op._schema.returns) == 0:
        if unwrapped_actual_out[0] is not None:
            raise AssertionError(
                f"Expected None for op with no returns, got {unwrapped_actual_out[0]}"
            )
        unwrapped_actual_out = None
    elif len(op._schema.returns) == 1:
        if len(unwrapped_actual_out) != 1:
            raise AssertionError(f"Expected 1 output, got {len(unwrapped_actual_out)}")
        unwrapped_actual_out = unwrapped_actual_out[0]
    else:
        if len(unwrapped_actual_out) != len(op._schema.returns):
            raise AssertionError(
                f"Expected {len(op._schema.returns)} outputs, got {len(unwrapped_actual_out)}"
            )

    for name, unwrapped_out in zip(mutable_args_names, unwrapped_mutable_out):
        # Can be None if input was `Tensor(a!)?`
        if unwrapped_out is None:
            continue

        # We only handle Tensor or List[Tensor] here for now.
        def sync_update(o, orig_arg):
            ctx.replace(orig_arg, o)
            ctx.commit_update(orig_arg)
            ctx.sync(orig_arg)

        orig_arg = normalized_kwargs[name]

        if isinstance(unwrapped_out, torch.Tensor):
            sync_update(unwrapped_out, orig_arg)
        elif isinstance(unwrapped_out, list) and all(
            isinstance(o, torch.Tensor) for o in unwrapped_out
        ):
            if len(orig_arg) != len(unwrapped_out):
                raise AssertionError(
                    f"orig_arg length ({len(orig_arg)}) != unwrapped_out length ({len(unwrapped_out)})"
                )
            for orig_a, o in zip(orig_arg, unwrapped_out):
                sync_update(o, orig_a)
        else:
            raise RuntimeError(
                f"unsupported type for auto-functionalization: {unwrapped_out}"
            )

    return ctx.wrap_tensors(unwrapped_actual_out)