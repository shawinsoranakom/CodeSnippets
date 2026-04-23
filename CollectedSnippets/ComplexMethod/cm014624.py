def valuetype_type(
    t: Type,
    *,
    binds: ArgName,
    mutable: bool = True,
    symint: bool = False,
) -> NamedCType | None:
    if isinstance(t, BaseType):
        if t.name in (BaseTy.Tensor, BaseTy.Scalar):
            return None
        elif str(t) == "SymInt":
            if symint:
                return NamedCType(binds, BaseCType(SymIntT))
            else:
                return NamedCType(binds, BaseCType(longT))
        # All other BaseType currently map directly to BaseCppTypes.
        return NamedCType(binds, BaseCType(BaseTypeToCppMapping[t.name]))
    elif isinstance(t, OptionalType):
        elem = valuetype_type(t.elem, binds=binds, mutable=mutable, symint=symint)
        if elem is None:
            return None
        return NamedCType(binds, OptionalCType(elem.type))
    elif isinstance(t, ListType):
        if str(t.elem) == "bool":
            if t.size is None:
                raise AssertionError("bool ListType must have a size")
            return NamedCType(binds, ArrayCType(BaseCType(boolT), t.size))
        else:
            return None
    else:
        raise AssertionError(f"unrecognized type {repr(t)}")