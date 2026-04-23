def generic_float(tx: "InstructionTranslator", obj: VariableTracker) -> VariableTracker:
    """Mirrors PyNumber_Float (float(x) dispatch).

    https://github.com/python/cpython/blob/v3.13.0/Objects/abstract.c#L1635-L1692

    Resolution: nb_float → nb_index → str parsing → TypeError.
    """
    from .constant import ConstantVariable

    # Fast path: if the value is already a float constant, return it directly.
    # Mirrors PyFloat_CheckExact fast path at the top of PyNumber_Float
    # (abstract.c:1641-1643).
    if obj.is_python_constant() and isinstance(obj.as_python_constant(), float):
        return ConstantVariable.create(float(obj.as_python_constant()))

    obj_type = maybe_get_python_type(obj)

    if type_implements_nb_float(obj_type):
        return obj.nb_float_impl(tx)

    # https://github.com/python/cpython/blob/v3.13.0/Objects/abstract.c#L1674-L1685
    if type_implements_nb_index(obj_type):
        return obj.nb_index_impl(tx)

    # PyFloat_FromString fallback — handles str and bytes.
    # https://github.com/python/cpython/blob/v3.13.0/Objects/abstract.c#L1691
    if obj.is_python_constant() and isinstance(obj.as_python_constant(), (str, bytes)):
        try:
            return ConstantVariable.create(float(obj.as_python_constant()))
        except ValueError as e:
            raise_observed_exception(ValueError, tx, args=[str(e)])

    raise_type_error(
        tx,
        f"float() argument must be a string or a real number, "
        f"not '{obj.python_type_name()}'",
    )