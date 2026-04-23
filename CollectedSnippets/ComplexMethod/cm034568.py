def _parse_atom(tokens, pos, variables):
    if pos >= len(tokens):
        raise ValueError("Unexpected end of condition expression")

    kind, value = tokens[pos]
    pos += 1

    if kind == "float":
        return float(value), pos
    elif kind == "int":
        return int(value), pos
    elif kind == "id":
        # Legacy alias: "get_quota.balance" → "quota.balance"
        if value == "get_quota.balance":
            value = "quota.balance"

        # Resolve dotted paths: "quota.credits.remaining", "balance", etc.
        parts = value.split(".")
        root = parts[0]
        if root not in variables:
            raise ValueError(f"Unknown variable in condition: {root!r}")

        result = variables[root]
        for part in parts[1:]:
            if isinstance(result, dict):
                result = result.get(part)
                if result is None:
                    result = 0.0
                    break
            else:
                raise ValueError(
                    f"Cannot access field {part!r} on non-dict value "
                    f"while resolving {value!r}"
                )

        return float(result) if result is not None else 0.0, pos
    else:
        raise ValueError(f"Unexpected token {kind!r}={value!r} in condition expression")