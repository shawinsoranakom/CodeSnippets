def generic_int(tx: "InstructionTranslator", obj: VariableTracker) -> VariableTracker:
    """Mirrors PyNumber_Long (int(x) dispatch).

    https://github.com/python/cpython/blob/v3.13.0/Objects/abstract.c#L1520-L1632

    Resolution: nb_int → nb_index → str/bytes/bytearray parsing → TypeError.
    """
    from .constant import ConstantVariable

    # Fast path for int (sub)class instances — mirrors PyLong_Check at the
    # top of PyNumber_Long (abstract.c:1531). Avoids infinite recursion for
    # int subclasses like IntEnum whose __int__ calls int() again.
    if obj.is_python_constant() and isinstance(obj.as_python_constant(), int):
        return ConstantVariable.create(int(obj.as_python_constant()))

    obj_type = maybe_get_python_type(obj)

    if type_implements_nb_int(obj_type):
        return obj.nb_int_impl(tx)

    if type_implements_nb_index(obj_type):
        return obj.nb_index_impl(tx)

    # String/bytes/bytearray parsing fallback.
    # https://github.com/python/cpython/blob/v3.13.0/Objects/abstract.c#L1598-L1612
    if obj.is_python_constant() and isinstance(
        obj.as_python_constant(), (str, bytes, bytearray)
    ):
        try:
            return ConstantVariable.create(int(obj.as_python_constant()))
        except ValueError as e:
            raise_observed_exception(ValueError, tx, args=[str(e)])

    raise_type_error(
        tx,
        f"int() argument must be a string, a bytes-like object "
        f"or a real number, not '{obj.python_type_name()}'",
    )