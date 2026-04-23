def _validate_out_schema(schema: "str | torch._C.FunctionSchema") -> None:
    """Validate that a schema has valid out semantics, i.e., it can be tagged with torch.Tag.out.

    Requirements:
    - Must have at least one mutable argument
    - All returns must alias the mutable args in declaration order

    torchgen has equivalent checks (torchgen/model.py), but we reimplement them here
    because (1) it's simple and (2) torchgen uses a different schema object
    (torchgen.model.FunctionSchema vs torch._C.FunctionSchema) so it's difficult to
    share the function.
    """
    if isinstance(schema, str):
        schema = torch._C.parse_schema(schema)
    mutable_args = [
        arg
        for arg in schema.arguments
        if arg.alias_info is not None and arg.alias_info.is_write
    ]
    if not mutable_args:
        raise ValueError(
            f"Schema tagged with torch.Tag.out must have at least one mutable argument. "
            f"Got: {schema}"
        )
    positional_mutable = [arg for arg in mutable_args if not arg.kwarg_only]
    if positional_mutable:
        names = [a.name for a in positional_mutable]
        raise ValueError(
            f"Schema tagged with torch.Tag.out requires all mutable arguments to be "
            f"keyword-only (after the *). Found mutable positional args: {names}. "
            f"Got: {schema}"
        )
    unsupported_mutable = [
        arg
        for arg in mutable_args
        if isinstance(arg.type, (torch.OptionalType, torch.ListType))
    ]
    if unsupported_mutable:
        names = [a.name for a in unsupported_mutable]
        raise ValueError(
            f"Schema tagged with torch.Tag.out only supports Tensor mutable arguments. "
            f"Found unsupported mutable args: {names}. Got: {schema}"
        )
    returns = schema.returns
    if len(returns) != len(mutable_args):
        raise ValueError(
            f"Schema tagged with torch.Tag.out must return all mutable arguments "
            f"(got {len(mutable_args)} mutable args but {len(returns)} returns). "
            f"Got: {schema}"
        )
    for i, (ret, arg) in enumerate(zip(returns, mutable_args, strict=True)):
        arg_alias = arg.alias_info
        ret_alias = ret.alias_info
        if ret_alias is None:
            raise ValueError(
                f"Return {i} of schema tagged with torch.Tag.out must alias mutable arg '{arg.name}'. "
                f"Got: {schema}"
            )
        if not ret_alias.is_write:
            raise ValueError(
                f"Return {i} of schema tagged with torch.Tag.out must be a mutable alias "
                f"(e.g., Tensor(a!), not Tensor(a)) of arg '{arg.name}'. "
                f"Got: {schema}"
            )
        # arg_alias is guaranteed non-None by the mutable_args filter above
        if ret_alias.before_set != arg_alias.before_set:  # type: ignore[union-attr]
            raise ValueError(
                f"Return {i} of schema tagged with torch.Tag.out must alias mutable arg '{arg.name}' "
                f"(return aliases {ret_alias.before_set} but arg aliases {arg_alias.before_set}). "  # type: ignore[union-attr]
                f"Got: {schema}"
            )