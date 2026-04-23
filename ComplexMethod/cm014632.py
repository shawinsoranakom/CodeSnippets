def argument_type_str(
    t: Type, *, simple_type: bool = False, symint: bool = True
) -> str:
    if isinstance(t, BaseType):
        if t.name == BaseTy.int:
            return "int64_t"
        elif t.name == BaseTy.float:
            return "double"
        elif t.name == BaseTy.str:
            return "c10::string_view"
        elif t.name in [
            BaseTy.Tensor,
            BaseTy.bool,
            BaseTy.QScheme,
            BaseTy.Scalar,
            BaseTy.ScalarType,
            BaseTy.Generator,
            BaseTy.Storage,
            BaseTy.Layout,
            BaseTy.Device,
            BaseTy.DeviceIndex,
            BaseTy.MemoryFormat,
            BaseTy.Dimname,
            BaseTy.Stream,
            BaseTy.SymInt,
        ]:
            # These python schema type names line up with their function schema names
            return t.name.name

    elif isinstance(t, OptionalType):
        elem = argument_type_str(t.elem, simple_type=simple_type, symint=symint)
        return f"{elem}?"
    elif isinstance(t, ListType):
        size = t.size if not simple_type else None
        if str(t.elem) == "bool":
            if t.size is None:
                raise AssertionError("bool ListType must have a size")
            return f"::std::array<bool,{t.size}>"
        elif str(t.elem) == "int":
            return f"IntArrayRef[{size}]" if size is not None else "IntArrayRef"
        elif str(t.elem) == "SymInt":
            if symint:
                return (
                    f"SymIntArrayRef[{size}]" if size is not None else "SymIntArrayRef"
                )
            else:
                return f"IntArrayRef[{size}]" if size is not None else "IntArrayRef"
        elif str(t.elem) == "Tensor":
            return f"TensorList[{size}]" if size is not None else "TensorList"
        elif str(t.elem) == "Scalar":
            return f"ScalarList[{size}]" if size is not None else "ScalarList"
        elif str(t.elem) == "Tensor?":
            if simple_type:
                return "c10::List<::std::optional<Tensor>>"
            else:
                return "const c10::List<::std::optional<Tensor>> &"
        elif str(t.elem) == "Dimname":
            return f"DimnameList[{size}]" if size is not None else "DimnameList"
        elem = argument_type_str(t.elem, simple_type=simple_type, symint=symint)
        return f"ArrayRef<{elem}>"

    raise RuntimeError(f"unrecognized type {repr(t)}")