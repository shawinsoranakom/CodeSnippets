def _get_code_source(code: types.CodeType) -> tuple[str, str]:
    """
    Given a code object, return a fully qualified name which will be used as
    a serialized handle to access the code object from the new process.
    This is normally a straightforward process, but there are some corner cases:
    1. When a function is defined with decorator, then this function will be captured
       inside a closure with the wrapper object.
    2. When a function is defined as a nested function, then the code object will be
       stored on the co_consts field of the parent code object by Python compiler.
    This function handles all of the corner cases above.
    """

    module = inspect.getmodule(code)
    if module is None:
        raise PackageError(f"Cannot find module for code {code}")

    toplevel: Any = module
    if sys.version_info >= (3, 11):
        parts = code.co_qualname.split(".")

        for part in parts:
            if not hasattr(toplevel, part):
                _raise_resolution_error(code, toplevel)
            toplevel = getattr(toplevel, part)
            if inspect.isfunction(toplevel) or inspect.ismethod(toplevel):
                break
    seen = set()

    def _find_code_source(obj: Any) -> str | None:
        nonlocal toplevel
        nonlocal seen
        if obj in seen:
            return None

        seen.add(obj)

        if inspect.iscode(obj):
            if obj is code:
                return ""

            for i, const in enumerate(obj.co_consts):
                if (res := _find_code_source(const)) is not None:
                    return f".co_consts[{i}]{res}"

        if inspect.ismethod(obj):
            if (res := _find_code_source(obj.__func__)) is not None:
                toplevel = obj
                return f".__func__{res}"

        if inspect.isfunction(obj):
            if (res := _find_code_source(obj.__code__)) is not None:
                toplevel = obj
                return f".__code__{res}"
            if obj.__closure__ is not None:
                for i, cell in enumerate(obj.__closure__):
                    try:
                        cell_contents = cell.cell_contents
                    except ValueError:
                        continue
                    if not (
                        inspect.isfunction(cell_contents)
                        or inspect.iscode(cell_contents)
                        or inspect.ismethod(cell_contents)
                    ):
                        continue
                    if (res := _find_code_source(cell_contents)) is not None:
                        toplevel = obj
                        return f".__closure__[{i}].cell_contents{res}"

        if sys.version_info < (3, 11):
            if inspect.ismodule(obj):
                for value in obj.__dict__.values():
                    if not (
                        inspect.isfunction(value)
                        or inspect.isclass(value)
                        or inspect.ismethod(value)
                    ):
                        continue
                    if (res := _find_code_source(value)) is not None:
                        return res

            if inspect.isclass(obj):
                for name in itertools.chain(obj.__dict__.keys(), dir(obj)):
                    try:
                        value = getattr(obj, name)
                    except AttributeError:
                        continue
                    if not (
                        inspect.isfunction(value)
                        or inspect.isclass(value)
                        or inspect.ismethod(value)
                    ):
                        continue
                    if (res := _find_code_source(value)) is not None:
                        if value.__name__ != name:
                            _raise_resolution_error(code, toplevel)
                        return res
        return None

    code_source = _find_code_source(toplevel)
    if code_source is None:
        _raise_resolution_error(code, toplevel)
    return toplevel.__qualname__, code_source.strip(".")