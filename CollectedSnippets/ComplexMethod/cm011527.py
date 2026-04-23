def resolve_op_names(patterns: list[str]) -> list[str]:
    """Resolve user-provided op patterns to exact OpInfo names.

    Supports exact names, comma separation, and glob patterns (e.g.,
    "nn.functional.*"). Short names like "relu" are resolved unambiguously
    or an error is raised with suggestions.
    """
    all_opinfo_names = sorted({op.name for op in op_db})
    resolved: list[str] = []
    seen: set[str] = set()

    for pattern in patterns:
        # Glob pattern
        if "*" in pattern or "?" in pattern:
            matches = fnmatch.filter(all_opinfo_names, pattern)
            if not matches:
                raise ValueError(f'No OpInfo names match pattern "{pattern}".')
            for m in matches:
                if m not in seen:
                    resolved.append(m)
                    seen.add(m)
            continue

        # Exact match
        if pattern in {op.name for op in op_db}:
            if pattern not in seen:
                resolved.append(pattern)
                seen.add(pattern)
            continue

        # Try to resolve shorthand
        candidates = _find_opinfo_candidates(pattern)
        if len(candidates) == 1:
            name = candidates[0]
            if name not in seen:
                resolved.append(name)
                seen.add(name)
        elif len(candidates) > 1:
            suggestions = ", ".join(f'"{c}"' for c in candidates)
            raise ValueError(
                f'"{pattern}" is ambiguous, matching: {suggestions}. '
                f"Use the fully qualified name."
            )
        else:
            raise ValueError(f'No OpInfo found for "{pattern}".')

    return resolved