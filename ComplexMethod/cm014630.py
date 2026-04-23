def argumenttype_type(t: Type, *, mutable: bool, binds: ArgName) -> NamedCType:
    # If it's a value type, do the value type translation
    # NB: structured kernels ALWAYS have symint off, since they involve actual
    # kernels that require real ints.  The one exception is the
    # CompositeExplicitAutograd and the meta function (which could
    # hypothetically be SymInt), but for simplicity we plan for these to just
    # be handled in Python
    r = cpp.valuetype_type(t, symint=False, binds=binds, mutable=mutable)
    if r is not None:
        return r

    if isinstance(t, BaseType):
        if t.name == BaseTy.Tensor:
            return NamedCType(binds, ConstRefCType(BaseCType(tensorT)))
        elif t.name == BaseTy.Scalar:
            return NamedCType(binds, ConstRefCType(BaseCType(scalarT)))
        else:
            raise AssertionError(f"base type should have been value type {t}")
    elif isinstance(t, OptionalType):
        if t.elem == BaseType(BaseTy.Tensor):
            return NamedCType(binds, BaseCType(optionalTensorRefT))
        elif t.elem == BaseType(BaseTy.Scalar):
            return NamedCType(binds, BaseCType(optionalScalarRefT))
        elif isinstance(t.elem, ListType) and str(t.elem.elem) == "int":
            return NamedCType(binds, BaseCType(optionalIntArrayRefT))
        elem = argumenttype_type(t.elem, mutable=mutable, binds=binds)
        return NamedCType(binds, OptionalCType(elem.type))
    elif isinstance(t, ListType):
        if t.elem == BaseType(BaseTy.Tensor):
            return NamedCType(binds, ConstRefCType(BaseCType(iTensorListRefT)))
        elif t.elem == OptionalType(BaseType(BaseTy.Tensor)):
            return NamedCType(binds, BaseCType(iOptTensorListRefT))
        # TODO: delete these special cases; see torchgen.api.cpp--these
        # must be changed in tandem, but there are problems; see
        # https://github.com/pytorch/pytorch/pull/51485
        elif str(t.elem) == "int":
            return NamedCType(binds, BaseCType(intArrayRefT))
        elif str(t.elem) == "Dimname":
            return NamedCType(binds, BaseCType(dimnameListT))
        elem = argumenttype_type(t.elem, mutable=mutable, binds=binds)
        return NamedCType(binds, ArrayRefCType(elem.type))
    else:
        raise AssertionError(f"unrecognized type {repr(t)}")