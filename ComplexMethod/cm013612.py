def _maybe_get_inplace_op(op: object) -> torch._ops.OpOverload | None:
    # __module__ seems broken; it returns torch._ops.aten which doesn't exist
    if not isinstance(op, torch._ops.OpOverload):
        return None
    # Some view ops have inplace variants (as_strided_, etc),
    # but we do NOT want the reinplacing pass to directly add these into the program.
    # (they'll require extra special handling, aren't aren't really useful for perf anyway)
    if _is_view_op(op):
        return None
    op_namespace = op.__module__.split(".")[-1]
    op_base_name = op.overloadpacket.__name__
    maybe_namespace_module = getattr(torch.ops, op_namespace)
    maybe_inplace_op = (
        None
        if maybe_namespace_module is None
        else getattr(maybe_namespace_module, f"{op_base_name}_", None)
    )
    if maybe_inplace_op is None:
        return None

    inplace_overloads = [
        getattr(maybe_inplace_op, overload_name)
        for overload_name in maybe_inplace_op.overloads()
    ]
    inplace_overloads_with_matching_schemas = [
        f for f in inplace_overloads if _schemas_match(op._schema, f._schema)
    ]
    # Just because foo() and foo_() are both existing operators,
    # They aren't guaranteed to have compatible schemas.
    # For example, pow.Scalar(Scalar self, Tensor exponent) has no valid inplace variant,
    # Even though several overloads of pow_ exist.
    if len(inplace_overloads_with_matching_schemas) == 0:
        return None
    if len(inplace_overloads_with_matching_schemas) != 1:
        raise AssertionError(
            f"Expected exactly 1 matching inplace overload, got "
            f"{len(inplace_overloads_with_matching_schemas)}"
        )
    inplace_op = inplace_overloads_with_matching_schemas[0]
    return inplace_op