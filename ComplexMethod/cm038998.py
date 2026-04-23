def parse_compute_capability(node: ast.ClassDef) -> str:
    """Parse supports_compute_capability method."""
    method = find_method(node, "supports_compute_capability")
    if method is None:
        return "Any"

    min_cap: tuple[int, int] | None = None
    max_cap: tuple[int, int] | None = None
    major_list: list[int] = []

    for n in ast.walk(method):
        if not isinstance(n, ast.Compare):
            continue

        # Handle `capability >= DeviceCapability(...)` or `capability <= ...`
        for op, comp in zip(n.ops, n.comparators):
            if not (
                isinstance(comp, ast.Call)
                and isinstance(comp.func, ast.Name)
                and comp.func.id == "DeviceCapability"
                and comp.args
                and isinstance(comp.args[0], ast.Constant)
            ):
                continue
            major = comp.args[0].value
            minor = 0
            if len(comp.args) > 1 and isinstance(comp.args[1], ast.Constant):
                minor = comp.args[1].value
            if isinstance(op, ast.GtE):
                min_cap = (major, minor)
            elif isinstance(op, ast.LtE):
                max_cap = (major, minor)

        # Handle `capability.major == N` or `capability.major in [N, M]`
        if (
            isinstance(n.left, ast.Attribute)
            and n.left.attr == "major"
            and len(n.ops) == 1
            and len(n.comparators) == 1
        ):
            comp = n.comparators[0]
            if isinstance(n.ops[0], ast.Eq) and isinstance(comp, ast.Constant):
                major_list.append(comp.value)
            elif isinstance(n.ops[0], ast.In) and isinstance(comp, ast.List):
                major_list.extend(
                    e.value
                    for e in comp.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, int)
                )

    if major_list:
        major_list.sort()
        if len(major_list) == 1:
            return f"{major_list[0]}.x"
        return f"{major_list[0]}.x-{major_list[-1]}.x"

    if min_cap:
        if max_cap:
            return f"{min_cap[0]}.x-{max_cap[0]}.x"
        return f"≥{min_cap[0]}.{min_cap[1]}"

    return "Any"