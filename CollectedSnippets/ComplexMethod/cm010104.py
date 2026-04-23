def parseNestedExpr(expr: str, module: Any) -> tuple[Any, int]:
        i = 0
        while i < len(expr) and expr[i] not in (",", "[", "]"):
            i += 1

        # Special case logic for the empty Tuple as a subscript (used
        # in the type annotation `Tuple[()]`)
        if expr[:i] == "()":
            return (), i

        base = lookupInModule(expr[:i].strip(), module)
        if base is None:
            raise AssertionError(f"Unresolvable type {expr[:i]}")
        if i == len(expr) or expr[i] != "[":
            return base, i

        if expr[i] != "[":
            raise AssertionError(f"expected '[' at position {i}, got {expr[i]!r}")
        parts = []
        while expr[i] != "]":
            part_len = 0
            i += 1
            part, part_len = parseNestedExpr(expr[i:], module)
            parts.append(part)
            i += part_len
        if len(parts) > 1:
            return base[tuple(parts)], i + 1
        else:
            return base[parts[0]], i + 1