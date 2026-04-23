def get_alias_info(func) -> SchemaInfo:
    # For ATen ops: use torchgen (since torchscript parser doesn't handle alias annotations
    # properly for some ops that output tensorlists)
    if func.namespace == "aten":
        torchgen_schema_str = str(func._schema)
        if not torchgen_schema_str.startswith("aten::"):
            raise AssertionError(
                "Expected torchgen schema string to start with 'aten::'"
            )
        # remove the aten:: namespace, which is added by the torchscript parser,
        # and torchgen doesn't know how to handle
        torchgen_schema_str = torchgen_schema_str[6:]
        import re

        # the torchscript parser ends up converting int[2]=1 into int[2]=[1, 1],
        # which torchgen chokes on.
        torchgen_schema_str = re.sub(r"=\[[0, ]+\]", "=0", torchgen_schema_str)
        torchgen_schema_str = re.sub(r"=\[[1, ]+\]", "=1", torchgen_schema_str)
        # for aten::rot90 / aten:fft_*
        torchgen_schema_str = re.sub(
            r"=\[(-?[0-9]+), (-?[0-9]+)\]", r"=[\1,\2]", torchgen_schema_str
        )
        torchgen_schema = torchgen.model.FunctionSchema.parse(torchgen_schema_str)
        arg_schemas = [
            AliasInfo(
                alias_set=(
                    set() if a.annotation is None else set(a.annotation.alias_set)
                ),
                is_write=a.annotation is not None and a.annotation.is_write,
                name=a.name,
            )
            for a in torchgen_schema.arguments.flat_all
        ]
        out_schemas = [
            AliasInfo(
                alias_set=(
                    set() if a.annotation is None else set(a.annotation.alias_set)
                ),
                is_write=a.annotation is not None and a.annotation.is_write,
                name=a.name,
            )
            for a in torchgen_schema.returns
        ]
    else:
        # For non-aten ops, torchgen is untested so we rely on torchscript schema parsing
        arg_schemas = [
            AliasInfo(
                alias_set=(
                    set() if a.alias_info is None else set(a.alias_info.before_set)
                ),
                is_write=a.alias_info is not None and a.alias_info.is_write,
                name=a.name,
            )
            for a in func._schema.arguments
        ]
        out_schemas = [
            AliasInfo(
                alias_set=(
                    set() if a.alias_info is None else set(a.alias_info.before_set)
                ),
                is_write=a.alias_info is not None and a.alias_info.is_write,
                name=a.name,
            )
            for a in func._schema.returns
        ]
    read_only_alias_match_indexes = []
    for arg_idx, schema_arg in enumerate(arg_schemas):
        for return_idx, schema_out in enumerate(out_schemas):
            is_read_only_alias_match = (
                schema_arg.alias_set & schema_out.alias_set
            ) and not schema_arg.is_write
            if is_read_only_alias_match:
                read_only_alias_match_indexes.append((arg_idx, return_idx))

    outs_write_aliases_list: list[str | None] = [
        _get_write_alias(r) for r in out_schemas
    ]
    non_nones = sum(x is not None for x in outs_write_aliases_list)
    if non_nones == 0:
        outs_write_aliases: list[str] | None = None
    elif non_nones != len(outs_write_aliases_list):
        # simplifying assumption: we don't have **any** ops with return types like "-> (Tensor(a!), Tensor)"
        raise RuntimeError("Unsupported schema: " + str(func._schema))
    else:
        outs_write_aliases = cast(list[str], outs_write_aliases_list)

    schema_info = SchemaInfo(
        args=arg_schemas,
        outs=out_schemas,
        # This check is surprisingly expensive because pybind11 enum_s are
        # inefficient. Just cache it.
        is_inplace_view_op=torch.Tag.inplace_view in func.tags,
        outs_write_aliases=outs_write_aliases,
        read_only_alias_match_indexes=read_only_alias_match_indexes,
    )
    return schema_info