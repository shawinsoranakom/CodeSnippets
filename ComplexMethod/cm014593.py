def node_ctor_arg_rvalue_string(arg: LazyArgument) -> str:
    """
    Given a LazyArgument,
    generate a c++ string for materializing an rvalue of that arg for passing into
    a lazy Node constructor.
    """

    # TODO: Matching on CType seems wrong; should be matching on Type
    if isValueType(arg.lazy_type):
        if isinstance(arg.lazy_type, BaseCType):
            if arg.is_wrapped_scalar:
                return f"node_{arg.name}"
            elif arg.lazy_type.type is tensorListValueT:
                return f"lazy_{arg.name}_tensorlist"
            elif arg.is_symint_or_list:
                return f"GetSymIntValue({arg.name})"
            return f"lazy_{arg.name}->GetIrValue()"
        elif isinstance(arg.lazy_type, OptionalCType):
            if arg.is_symint_or_list:
                # TODO: I don't understand when you should put lazy_ in the name
                # or not
                return f"{arg.name} ? std::make_optional(GetSymIntValue(*{arg.name})) : ::std::nullopt"
            elif arg.is_wrapped_scalar:
                return f"node_{arg.name}"
            return (
                f"lazy_{arg.name} ? "
                f"std::make_optional(lazy_{arg.name}->GetIrValue()) : "
                "::std::nullopt"
            )
        else:
            raise AssertionError(
                f"TODO not sure if there are other valid types to handle here ({arg.lazy_type})"
            )
    else:
        # NB: this is here because right now we aren't treating SymInt[] as a
        # value type; when we do this needs to move above
        # NB: we cannot test arg.lazy_type as we've already specified it is an
        # int64_t and so we cannot distinguish between SymInt and int64_t
        if isinstance(arg.orig_type, ListType) and arg.orig_type.elem == BaseType(
            BaseTy.SymInt
        ):
            if arg.symint:
                return f"GetSymIntArrayRefValue({arg.name})"
            else:
                return f"std::vector<int64_t>({arg.name}.begin(), {arg.name}.end())"
        elif isinstance(arg.lazy_type, VectorCType) and isinstance(
            arg.lazy_type.elem, BaseCType
        ):
            return f"std::vector<{arg.lazy_type.elem.type}>({arg.name}.begin(), {arg.name}.end())"
        elif (
            isinstance(arg.lazy_type, OptionalCType)
            and isinstance(arg.lazy_type.elem, VectorCType)
            and isinstance(arg.lazy_type.elem.elem, BaseCType)
        ):
            return f"torch::lazy::ToOptionalVector<{arg.lazy_type.elem.elem.type}>({arg.name})"
        else:
            return f"{arg.name}"