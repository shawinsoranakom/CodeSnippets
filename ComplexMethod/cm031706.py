def correct_name_for_self(
        f: Function,
        parser: bool = False
) -> tuple[str, str]:
    if f.kind in {CALLABLE, METHOD_INIT, GETTER, SETTER}:
        if f.cls:
            return "PyObject *", "self"
        return "PyObject *", "module"
    if f.kind is STATIC_METHOD:
        if parser:
            return "PyObject *", "null"
        else:
            return "void *", "null"
    if f.kind == CLASS_METHOD:
        if parser:
            return "PyObject *", "type"
        else:
            return "PyTypeObject *", "type"
    if f.kind == METHOD_NEW:
        return "PyTypeObject *", "type"
    raise AssertionError(f"Unhandled type of function f: {f.kind!r}")