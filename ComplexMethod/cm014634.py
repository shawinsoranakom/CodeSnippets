def argument_type_str_pyi(t: Type) -> str:
    add_optional = False
    if isinstance(t, OptionalType):
        t = t.elem
        add_optional = True

    ret = ""
    if isinstance(t, BaseType):
        if t.name in [BaseTy.int, BaseTy.DeviceIndex]:
            ret = "_int"
        if t.name == BaseTy.SymInt:
            ret = "_int | SymInt"
        elif t.name == BaseTy.float:
            ret = "_float"
        elif t.name == BaseTy.str:
            ret = "str"
        elif t.name == BaseTy.Scalar:
            ret = "Number | _complex"
        elif t.name == BaseTy.ScalarType:
            ret = "_dtype"
        elif t.name == BaseTy.bool:
            ret = "_bool"
        elif t.name == BaseTy.QScheme:
            ret = "_qscheme"
        elif t.name == BaseTy.Layout:
            ret = "_layout"
        elif t.name == BaseTy.Device:
            ret = "DeviceLikeType | None"
        elif t.name == BaseTy.MemoryFormat:
            ret = "memory_format"
        elif t.name == BaseTy.Dimname:
            ret = "str | EllipsisType | None"
        elif t.name == BaseTy.Storage:
            ret = "Storage | UntypedStorage"
        elif t.name in [BaseTy.Tensor, BaseTy.Generator, BaseTy.Stream]:
            # These python schema type names line up with their function schema names
            ret = t.name.name

    elif isinstance(t, ListType):
        if str(t.elem) == "int":
            ret = "_int | _size" if t.size is not None else "_size"
        elif t.is_tensor_like():
            # Tensor?[] translates to tuple[Tensor | None, ...] | list[Tensor | None] | None
            # Tensor[] translates to tuple[Tensor, ...] | list[Tensor]
            if isinstance(t.elem, OptionalType):
                add_optional = True
                elem_str = "Tensor | None"
            else:
                elem_str = "Tensor"
            ret = (
                f"Tensor | tuple[{elem_str}, ...] | list[{elem_str}]"
                if t.size is not None
                else f"tuple[{elem_str}, ...] | list[{elem_str}]"
            )
        elif str(t.elem) == "float":
            ret = "Sequence[_float]"
        elif str(t.elem) == "SymInt" and t.size is not None:
            elem = argument_type_str_pyi(t.elem)
            ret = f"{elem} | Sequence[{elem}]"
        else:
            elem = argument_type_str_pyi(t.elem)
            ret = f"Sequence[{elem}]"

    else:
        raise RuntimeError(f"unrecognized type {repr(t)}")

    if add_optional:
        ret = f"{ret} | None".replace(" | None | None", " | None")

    return ret