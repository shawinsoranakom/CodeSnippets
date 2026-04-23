def auto_functionalized_v2_dense(
    _mutable_op: _MutableOpType,
    _only_clone_these_bases: tuple[int, ...] | None = None,
    **kwargs: Any,
) -> tuple[Any, tuple[Tensor, ...]]:
    _all_bases: list[Tensor] = kwargs.pop("_all_bases", [])
    if _only_clone_these_bases is None:
        _only_clone_these_bases = tuple(range(len(_all_bases)))

    if isinstance(_mutable_op, OpOverload):
        schema: torch._C.FunctionSchema = _mutable_op._schema
    else:
        schema = pytree.tree_unflatten([], kwargs.pop("_op_schema")).schema

    if isinstance(_mutable_op, OpOverload):
        _callable_op: HopInstance | OpOverload = _mutable_op
    else:
        if not isinstance(schema, HopSchema):
            raise AssertionError(f"Expected HopSchema, got {type(schema)}")
        _callable_op = HopInstance(_mutable_op, schema)

    _is_out = isinstance(_mutable_op, OpOverload) and torch._library.utils.is_out(
        _mutable_op
    )

    op_kwargs_new, all_bases_new = _generate_new_op_kwargs_from_bases(
        schema,
        kwargs,
        _all_bases,
        _only_clone_these_bases,
        _is_out,
    )

    out = call_op(
        _callable_op,
        tuple(),
        op_kwargs_new,
    )

    if _is_out:
        return out  # type: ignore[return-value]

    if isinstance(out, tuple):
        return (*out, *all_bases_new)  # type: ignore[return-value]
    else:
        return (out, *all_bases_new)