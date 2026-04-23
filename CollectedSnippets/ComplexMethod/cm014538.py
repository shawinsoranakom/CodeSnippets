def compute_argument_yaml(
    a: Argument,
    *,
    schema_order: bool,
    kwarg_only_set: set[str],
    out_arg_set: set[str],
    name_to_field_name: dict[str, str],
) -> object:
    arg: dict[str, object] = {
        "annotation": str(a.annotation) if a.annotation else None,
        "dynamic_type": dynamic_type(a.type),
        "is_nullable": a.type.is_nullable(),
        "name": a.name,
        # legacy, report ints
        "type": cpp.argument_type(a, binds="__placeholder__", symint=False).cpp_type(),
    }
    if a.default is not None:
        arg["default"] = pythonify_default(
            cpp.default_expr(a.default, a.type, symint=False)
        )
    if a.name in kwarg_only_set:
        arg["kwarg_only"] = True
    if a.name in out_arg_set:
        arg["output"] = True
        arg["allocate"] = True
        # See Note [name and field_name]
        if a.name in name_to_field_name:
            arg["field_name"] = name_to_field_name[a.name]
    # Historically, booleans don't get their size recorded, because it
    # is already built into the cpp type (e.g., std::array<bool, 4>)
    l = a.type.is_list_like()
    if l is not None and l.size is not None and str(l.elem) != "bool":
        arg["size"] = l.size
    return arg