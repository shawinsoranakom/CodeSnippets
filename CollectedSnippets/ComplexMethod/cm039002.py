def _parse_fa4_supported_caps() -> str | None:
    """Parse flash_attn_interface.py for FA4 supported compute capabilities.

    Looks for `cc not in [9, 10, 11]` pattern in _is_fa4_supported().
    """
    fa_interface_file = (
        REPO_ROOT / "vllm" / "vllm_flash_attn" / "flash_attn_interface.py"
    )
    if not fa_interface_file.exists():
        return None

    try:
        tree = ast.parse(fa_interface_file.read_text())
    except Exception:
        return None

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef) or node.name != "_is_fa4_supported":
            continue
        for n in ast.walk(node):
            if not (
                isinstance(n, ast.Compare)
                and len(n.ops) == 1
                and isinstance(n.ops[0], ast.NotIn)
                and isinstance(n.comparators[0], ast.List)
            ):
                continue
            caps: list[int] = [
                e.value
                for e in n.comparators[0].elts
                if isinstance(e, ast.Constant) and isinstance(e.value, int)
            ]
            if caps:
                caps.sort()
                return f"{caps[0]}.x-{caps[-1]}.x"

    return None