def _schemas_match(
    functional_schema: torch._C.FunctionSchema, inplace_schema: torch._C.FunctionSchema
) -> bool:
    names_match = (
        inplace_schema.name.endswith("_")
        and inplace_schema.name[:-1] == functional_schema.name
    )
    arg_types_match = len(functional_schema.arguments) == len(
        inplace_schema.arguments
    ) and all(
        a1.type == a2.type
        for a1, a2 in zip(functional_schema.arguments, inplace_schema.arguments)
    )
    # for the inplace op, its first argument should be mutable
    if not (
        inplace_schema.arguments[0].alias_info is not None
        and inplace_schema.arguments[0].alias_info.is_write
    ):
        raise AssertionError("First argument of inplace op must be mutable")
    # and its remaining arguments shouldn't be.
    if not all(a.alias_info is None for a in inplace_schema.arguments[1:]):
        raise AssertionError("Remaining arguments of inplace op must not be mutable")
    return names_match and arg_types_match