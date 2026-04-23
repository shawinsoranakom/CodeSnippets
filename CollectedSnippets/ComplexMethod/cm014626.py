def returntype_type(t: Type, *, mutable: bool, symint: bool = False) -> CType:
    # placeholder is ignored
    # NB: symint is ALWAYS respected for return types.  So symint argument
    # here is IGNORED
    r = valuetype_type(t, binds="__placeholder__", mutable=mutable, symint=True)
    if r is not None:
        return r.type

    if isinstance(t, BaseType):
        if t.name == BaseTy.Tensor:
            if mutable:
                if local.use_const_ref_for_mutable_tensors():
                    return ConstRefCType(BaseCType(tensorT))
                else:
                    return MutRefCType(BaseCType(tensorT))
            else:
                # Note [Tensor Copy Returns]
                # Currently, we use "Argument.is_write" to determine
                # whether or not Tensor return types should be copies or references.
                # If that ever changes, take a look at other locations of this note!
                return BaseCType(tensorT)
        elif t.name == BaseTy.Scalar:
            return BaseCType(scalarT)
    elif isinstance(t, ListType):
        if mutable:
            raise AssertionError(
                "Native functions should never return a mutable tensor list. "
                "They should return void."
            )
        elem = returntype_type(t.elem, mutable=False)
        if t.size is not None:
            raise AssertionError(f"fixed size list returns not supported: {t}")
        return VectorCType(elem)
    elif isinstance(t, OptionalType):
        elem = returntype_type(t.elem, mutable=mutable)
        if str(t.elem) == "Tensor":
            return OptionalCType(elem)

    raise AssertionError(f"unrecognized return type {t}")