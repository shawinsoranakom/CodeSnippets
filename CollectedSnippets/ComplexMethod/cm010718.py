def to_out_variant(op: torch._ops.OpOverload) -> torch._ops.OpOverload | None:
    """
    Given a functional operator overload, return its corresponding out variant.
    """
    schema = op._schema

    if not _is_functional(schema):
        raise RuntimeError(
            f"Failed to find out variant for op '{op}' as its schema is not functional. \n"
            f"  {schema}"
        )

    # Get the op packet to access all overloads
    namespace = op.namespace
    op_name = schema.name.split("::")[1]
    torch_packet = getattr(getattr(torch.ops, namespace), op_name)

    # Search through all overloads for matching out variant
    for overload_name in torch_packet.overloads():
        candidate = getattr(torch_packet, overload_name)

        # pyrefly: ignore [missing-attribute]
        if torch.Tag.out not in candidate.tags:
            continue

        candidate_schema = candidate._schema

        if not _signatures_match(schema, candidate_schema):
            continue

        # We assume that all mutable args are used for out
        mutable_args = [
            arg for arg in candidate_schema.arguments if _is_mutable_arg(arg)
        ]
        if len(mutable_args) != len(schema.returns):
            continue

        if not _has_valid_out_variant_returns(candidate_schema, mutable_args):
            raise RuntimeError(
                f"Out variant {candidate} has invalid returns. "
                f"Expected either no returns or returns that alias the mutable args, "
                f"got: {candidate_schema}"
            )

        return candidate

    return None