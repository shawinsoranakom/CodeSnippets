def default_expr(d: str, t: Type, *, symint: bool) -> str:
    if d == "None" and str(t) == "Tensor?":
        return "{}"
    if isinstance(t, BaseType) and t.name is BaseTy.str:
        # Schema allows single quotes but C++ needs double
        if len(d) >= 2 and d[0] == "'" and d[-1] == "'":
            s = ""
            i = 1
            while i + 1 < len(d):
                if d[i] != "\\":
                    if d[i] == '"':
                        s += '\\"'
                    else:
                        s += d[i]
                    i += 1
                else:
                    if d[i + 1] == "'":
                        s += "'"
                    else:
                        s += d[i : i + 2]
                    i += 2

            return f'"{s}"'

    if isinstance(t, OptionalType):
        if d == "None":
            return "::std::nullopt"

        return default_expr(d, t.elem, symint=symint)

    if isinstance(t, ListType):
        if d.startswith("[") and d.endswith("]"):
            return "{" + d[1:-1] + "}"
        elif symint and d.isdigit() and str(t.elem) == "SymInt":
            return f"c10::SymInt({d})"
        elif t.size is None:
            # NOTE: Sized lists can have scalar defaults
            raise ValueError(f"Expected a list default '[...]' but found: '{d}'")

    return JIT_TO_CPP_DEFAULT.get(d, d)