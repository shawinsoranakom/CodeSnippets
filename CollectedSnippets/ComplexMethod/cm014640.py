def isValueType(typ: CType, properties: LazyIrProperties | None = None) -> bool:
    """
    Given a type, determine if it is a Value-like type.  This is equivalent to
    being Tensor-like, but assumes the type has already been transformed.
    """
    if isinstance(typ, BaseCType):
        # I am regretting my naming conventions, but now we are wrapping at::scalar in
        # lazy value, while preserving other 'scalar' types as scalars in the IR
        treat_scalars_as_constants = properties and properties.TreatScalarsAsConstants
        return (
            typ.type == getValueT()
            or (typ.type == scalarT and not treat_scalars_as_constants)
            or typ.type == SymIntT
        )
    elif typ == VectorCType(BaseCType(SymIntT)):
        # TODO: report True for this
        return False
    elif isinstance(typ, (OptionalCType, ListCType, VectorCType)):
        return isValueType(typ.elem, properties)
    return False