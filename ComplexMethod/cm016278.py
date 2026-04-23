def sig_for_ops(opname: str) -> list[str]:
    """sig_for_ops(opname : str) -> list[str]

    Returns signatures for operator special functions (__add__ etc.)"""

    # we have to do this by hand, because they are hand-bound in Python

    if not (opname.endswith("__") and opname.startswith("__")):
        raise AssertionError(f"Unexpected op {opname}")

    name = opname[2:-2]
    if name == "rpow":
        return [  # somehow required to make mypy ci happy?
            f"def {opname}(self, other: Tensor | Number | _complex) -> Tensor: ...  # type: ignore[has-type]"
        ]
    elif name in arithmetic_ops:
        if name.startswith("i"):
            # In-place binary-operation dunder methods, like `__iadd__`, should return `Self`.
            # `__idiv__` is not a real Python 3 in-place dunder (Python 3 uses `__itruediv__` /
            # `__ifloordiv__`), so ruff's PYI034 doesn't fire on it and the noqa would be unused.
            suffix = "" if name == "idiv" else "  # noqa: PYI034"
            return [
                f"def {opname}(self, other: Tensor | Number | _complex) -> Tensor: ...{suffix}"
            ]
        return [f"def {opname}(self, other: Tensor | Number | _complex) -> Tensor: ..."]
    elif name in logic_ops:
        return [f"def {opname}(self, other: Tensor | _int) -> Tensor: ..."]
    elif name in shift_ops:
        return [f"def {opname}(self, other: Tensor | _int) -> Tensor: ..."]
    elif name in symmetric_comparison_ops:
        return [
            # unsafe override https://github.com/python/mypy/issues/5704
            f"def {opname}(self, other: Tensor | Number | _complex) -> Tensor: ...  # type: ignore[overload-overlap]",
            f"def {opname}(self, other: object) -> _bool: ...",
        ]
    elif name in asymmetric_comparison_ops:
        return [f"def {opname}(self, other: Tensor | Number | _complex) -> Tensor: ..."]
    elif name in unary_ops:
        return [f"def {opname}(self) -> Tensor: ..."]
    if name in to_py_type_ops:
        if name in {"bool", "float", "complex"}:
            tname = name
        elif name == "nonzero":
            tname = "bool"
        else:
            tname = "int"
        if tname in {"float", "int", "bool", "complex"}:
            tname = "_" + tname
        return [f"def {opname}(self) -> {tname}: ..."]
    raise ValueError(f"unknown op {opname!r}")