def _do_auto_functionalize_v2_for_generic_mutable_operator(
    ctx: Any,
    op: Any,
    schema: Any,
    normalized_kwargs: dict[str, Any],
) -> Any:
    """Handle functionalization for generic mutable operators via the
    auto_functionalized_v2 HOP."""
    mutable_args_names, mutable_args_types = get_mutable_args_from_schema(schema)

    # A list of all bases of mutable args without duplication
    all_bases: list[Any] = []
    all_bases_addresses: list[int] = []

    # Map arg_name to the index of its base in all_bases.
    arg_to_base_index: dict[str, Any] = {}

    def update_dict(tensor, arg_name, index=None):
        base = tensor if get_base(tensor) is None else get_base(tensor)

        def set_result(base_index):
            if index is None:
                arg_to_base_index[arg_name] = base_index
            else:
                arg_to_base_index[arg_name][index] = base_index

        if not all_bases_addresses.__contains__(base._cdata):
            all_bases_addresses.append(base._cdata)
            all_bases.append(base)
            set_result(len(all_bases) - 1)
        else:
            set_result(all_bases_addresses.index(base._cdata))

    for arg_name in mutable_args_names:
        arg = normalized_kwargs[arg_name]
        if arg is None:
            continue

        if isinstance(arg, list):
            arg_to_base_index[arg_name] = {}
            for i, tensor in enumerate(arg):
                if tensor is None:
                    arg_to_base_index[arg_name].append(None)
                    continue

                update_dict(tensor, arg_name, i)

        else:
            update_dict(arg, arg_name)

    # add view_meta for each args into unwrapped_kwargs.
    write_view_information_to_args(
        mutable_args_names,
        mutable_args_types,
        normalized_kwargs,
        arg_to_base_index,
    )

    # remove mutated args from the kwargs (its a function of _all_bases now)
    for arg_name in mutable_args_names:
        del normalized_kwargs[arg_name]  # type: ignore[arg-type]

    unwrapped_kwargs = ctx.unwrap_tensors(normalized_kwargs)  # type: ignore[arg-type]
    if "self" in unwrapped_kwargs or "self_" in unwrapped_kwargs:
        warnings.warn(
            "Using `self` or `self_` as an argument in the definition of custom ops may lead to ambiguous parsing. "
            "Please consider using a different name for this argument to avoid potential issues.",
            stacklevel=2,
        )
    all_basis_unwrapped = ctx.unwrap_tensors(all_bases)

    if "_all_bases" in unwrapped_kwargs:
        raise AssertionError(f"_all_bases already in unwrapped_kwargs for {op}")
    auto_func_kwargs = dict(unwrapped_kwargs, _all_bases=all_basis_unwrapped)
    if isinstance(op, HigherOrderOperator):
        if "_ops_schema" in unwrapped_kwargs:
            raise AssertionError(f"_ops_schema already in unwrapped_kwargs for {op}")
        # We pass in the tree_spec of tree_flatten(SchemaHolder) to make it proxable
        auto_func_kwargs.update(
            {"_op_schema": pytree.tree_flatten(SchemaHolder(schema))[1]}
        )

    with ctx.redispatch_to_next():
        unwrapped_outs = auto_functionalized_v2(
            op,
            **auto_func_kwargs,  # type: ignore[arg-type]
        )

    unwrapped_actual_out: Any | tuple[Any] = (
        unwrapped_outs if len(all_bases) == 0 else unwrapped_outs[: -len(all_bases)]
    )

    unwrapped_mutable_out = (
        [] if len(all_bases) == 0 else unwrapped_outs[-len(all_bases) :]
    )

    if isinstance(op, HigherOrderOperator):
        if len(schema.returns) <= 0:
            raise AssertionError(
                f"hop is expected to return at least one output {schema}."
            )
        if len(unwrapped_actual_out) != len(schema.returns):
            raise AssertionError(
                f"Expected {len(schema.returns)} outputs, got {len(unwrapped_actual_out)}"
            )
    else:
        if len(schema.returns) == 0:
            if unwrapped_actual_out[0] is not None:
                raise AssertionError(
                    f"Expected None for op with no returns, got {unwrapped_actual_out[0]}"
                )
            unwrapped_actual_out = None
        elif len(schema.returns) == 1:
            if len(unwrapped_actual_out) != 1:
                raise AssertionError(
                    f"Expected 1 output, got {len(unwrapped_actual_out)}"
                )
            unwrapped_actual_out = unwrapped_actual_out[0]
        else:
            if len(unwrapped_actual_out) != len(schema.returns):
                raise AssertionError(
                    f"Expected {len(schema.returns)} outputs, got {len(unwrapped_actual_out)}"
                )

    for orig_arg, unwrapped_out in zip(all_bases, unwrapped_mutable_out):
        # Can be None if input was `Tensor(a!)?`
        if unwrapped_out is None:
            continue

        # We only handle Tensor or List[Tensor] here for now.
        def sync_update(o, orig_arg):
            ctx.replace(orig_arg, o)
            ctx.commit_update(orig_arg)
            ctx.sync(orig_arg)

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