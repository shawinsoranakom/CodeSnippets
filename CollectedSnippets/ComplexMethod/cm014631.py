def format_function_signature(
    name: str, arguments: Iterable[str] = (), return_type: str | None = None
) -> str:
    if not isinstance(arguments, (list, tuple)):
        arguments = tuple(arguments)
    return_type = f" -> {return_type}" if return_type is not None else ""

    sig = f"def {name}({', '.join(arguments)}){return_type}: ..."
    if len(sig) <= 80 or len(arguments) == 0 or tuple(arguments) == ("self",):
        return sig

    lines = [
        f"def {name}(",
        *(f"    {arg}," for arg in arguments),
        f"){return_type}: ...",
    ]
    sig = "\n".join(lines)
    if all(len(line) <= 80 for line in lines):
        return sig
    # ruff format bug for compound statements: https://github.com/astral-sh/ruff/issues/18658
    # use `skip` instead of `on` + `off`
    return sig.removesuffix(" ...") + "  # fmt: skip\n    ..."