def _infer_schema_info_from_op(op: OpOverload) -> RuntimeSchemaInfo:
    """Infer RuntimeSchemaInfo from an operator's schema for decomposition ops"""
    schema = op._schema

    # Find first non-tensor positional arg index
    static_argnum = None
    for i, arg in enumerate(schema.arguments):
        if arg.kwarg_only:
            break
        if arg.type.kind() != "TensorType" and static_argnum is None:
            static_argnum = i
            break

    # Find keyword-only args that aren't tensors
    kwarg_only_names = []
    for arg in schema.arguments:
        if arg.kwarg_only and arg.type.kind() != "TensorType":
            kwarg_only_names.append(arg.name)

    kwargs = {}
    if static_argnum is not None:
        kwargs["static_argnum"] = static_argnum
    if kwarg_only_names:
        # pyrefly: ignore [unsupported-operation]
        kwargs["static_kwargkey"] = kwarg_only_names

    # pyrefly: ignore [bad-argument-type]
    return RuntimeSchemaInfo(**kwargs)