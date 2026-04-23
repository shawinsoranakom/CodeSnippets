def can_auto_functionalize(
    op: OperatorBase | HopInstance,
) -> bool:
    if isinstance(op, HopInstance):
        # HOPs that implement gen_schema and schema is not functional are auto_functionalizable.
        if not _has_gen_schema(op._op):
            return False

    else:
        if not isinstance(op, OpOverload):
            return False

        if torch._library.utils.is_builtin(op):
            # We control the built-ins. These may (in rare cases)
            # do input metadata mutation (which we have banned on custom ops)
            return False

    schema = op._schema
    if not schema.is_mutable:
        return False
    schema = op._schema

    for arg in schema.arguments:
        if arg.alias_info is None:
            continue
        if not arg.alias_info.is_write:
            continue
        if torch._library.utils.is_tensor_like_type(arg.type):
            continue
        if torch._library.utils.is_tensorlist_like_type(arg.type):
            continue
        return False

    if len(schema.returns) == 1 and isinstance(schema.returns[0].type, torch.NoneType):
        # Skip schema returns -> None
        return True
    if isinstance(op, OpOverload):
        if torch._library.utils.is_out(op):
            # Out ops have aliased returns (returns alias the mutable args).
            # This is fine because the mutable args are write-only output buffers.
            pass
        else:
            # The returns of OpOverload must not alias anything
            for ret in schema.returns:
                if ret.alias_info is None and type(ret.type) is torch.TensorType:
                    continue
                # Not yet supported: List[Tensor] return.
                return False
        if torch._C._dispatch_has_kernel_for_dispatch_key(op.name(), "Functionalize"):
            return False
    return True