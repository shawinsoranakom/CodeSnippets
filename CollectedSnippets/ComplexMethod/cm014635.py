def arg_parser_unpack_method(
    t: Type, default: str | None, default_init: str | None, *, symint: bool = True
) -> str:
    has_default_init = default_init is not None
    if has_default_init and str(t) not in (
        "ScalarType?",
        "ScalarType",
        "Device",
        "Device?",
        "Layout",
        "Layout?",
        "bool",
        "bool?",
    ):
        raise RuntimeError(f"type '{t}' does not supported unpacking with default")

    if isinstance(t, BaseType):
        if t.name in [
            BaseTy.Tensor,
            BaseTy.Stream,
            BaseTy.Storage,
            BaseTy.Scalar,
            BaseTy.Dimname,
        ]:
            # These unpack methods line up with their schema names
            return t.name.name.lower()
        elif t.name == BaseTy.ScalarType:
            return "scalartypeWithDefault" if has_default_init else "scalartype"
        elif t.name == BaseTy.Device:
            return "deviceWithDefault" if has_default_init else "device"
        elif t.name == BaseTy.DeviceIndex:
            return "toInt64"
        elif t.name == BaseTy.int:
            return "toInt64"
        elif t.name == BaseTy.SymInt:
            return "toSymInt" if symint else "toInt64"
        elif t.name == BaseTy.bool:
            return "toBoolWithDefault" if has_default_init else "toBool"
        elif t.name == BaseTy.float:
            return "toDouble"
        elif t.name == BaseTy.str:
            return "stringView"
        elif t.name == BaseTy.Layout:
            return "layoutWithDefault" if has_default_init else "layout"
        elif t.name == BaseTy.MemoryFormat:
            return "memoryformat"

    elif isinstance(t, OptionalType):
        if str(t.elem) == "Tensor":
            return "optionalTensor"
        elif str(t.elem) == "Generator":
            return "generator"
        elif str(t.elem) == "Dimname[]":
            return "toDimnameListOptional"
        elif not has_default_init and default in (
            None,
            "None",
            "::std::nullopt",
            "std::nullopt",
        ):
            # If default is None: append 'Optional' to elem's unpacking method
            return (
                arg_parser_unpack_method(t.elem, None, None, symint=symint) + "Optional"
            )
        else:
            # Otherwise, load as underlying type with default
            return arg_parser_unpack_method(
                t.elem, default, default_init, symint=symint
            )

    elif isinstance(t, ListType):
        if str(t.elem) == "Tensor":
            # accept and use definite size
            return f"tensorlist_n<{t.size}>" if t.size is not None else "tensorlist"
        elif str(t.elem) == "Tensor?":
            return "list_of_optional_tensors"
        elif str(t.elem) == "Dimname":
            # accept definite size
            return "dimnamelist"
        elif str(t.elem) == "int":
            # accept definite size
            return "intlist"
        elif str(t.elem) == "float":
            return "doublelist"
        elif str(t.elem) == "SymInt":
            # accept definite size
            return "symintlist" if symint else "intlist"
        elif str(t.elem) == "Scalar":
            return "scalarlist"
    raise RuntimeError(f"type '{t}' is not supported by PythonArgParser")