def parse_flash_attn_features() -> dict[str, dict[str, Any]]:
    """Parse fa_utils.py to detect FA2 vs FA3 vs FA4 feature differences.

    Returns a dict with 'fa2', 'fa3', and 'fa4' keys containing their respective
    feature overrides for compute capability, KV cache dtypes, and sink support.
    """
    if not FA_UTILS_FILE.exists():
        return {}

    try:
        tree = ast.parse(FA_UTILS_FILE.read_text())
    except Exception:
        return {}

    # Analyze the functions to determine FA3-specific features
    fa3_supports_fp8 = False
    fa3_supports_sinks = False
    fa3_compute_cap: str | None = None
    fa4_compute_cap: str | None = None

    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue

        # Check flash_attn_supports_fp8 - looks for `get_flash_attn_version() == 3`
        if node.name == "flash_attn_supports_fp8":
            for n in ast.walk(node):
                if (
                    isinstance(n, ast.Compare)
                    and isinstance(n.left, ast.Call)
                    and isinstance(n.left.func, ast.Name)
                    and n.left.func.id == "get_flash_attn_version"
                ):
                    fa3_supports_fp8 = True
                    break

        # Check flash_attn_supports_sinks - looks for `get_flash_attn_version() == 3`
        if node.name == "flash_attn_supports_sinks":
            for n in ast.walk(node):
                if (
                    isinstance(n, ast.Compare)
                    and isinstance(n.left, ast.Call)
                    and isinstance(n.left.func, ast.Name)
                    and n.left.func.id == "get_flash_attn_version"
                ):
                    fa3_supports_sinks = True
                    break

        # Check get_flash_attn_version for FA3/FA4 compute capability
        if node.name == "get_flash_attn_version":
            for n in ast.walk(node):
                # Handle IfExp (ternary) with `device_capability.major == 9`
                if isinstance(n, ast.IfExp):
                    test = n.test
                    if isinstance(test, ast.BoolOp):
                        for val in test.values:
                            if (
                                isinstance(val, ast.Compare)
                                and isinstance(val.left, ast.Attribute)
                                and val.left.attr == "major"
                                and val.comparators
                                and isinstance(val.comparators[0], ast.Constant)
                            ):
                                fa3_compute_cap = f"{val.comparators[0].value}.x"
                                break

                # Handle If statements for FA3/FA4 detection
                # e.g. `if device_capability.major == 9` -> FA3
                #      `elif device_capability.major >= 10` -> FA4
                if isinstance(n, ast.If):
                    test = n.test
                    comparisons = (
                        [v for v in test.values if isinstance(v, ast.Compare)]
                        if isinstance(test, ast.BoolOp)
                        else [test]
                        if isinstance(test, ast.Compare)
                        else []
                    )
                    for comp in comparisons:
                        if not (
                            isinstance(comp.left, ast.Attribute)
                            and comp.left.attr == "major"
                            and comp.comparators
                            and isinstance(comp.comparators[0], ast.Constant)
                            and isinstance(comp.comparators[0].value, int)
                        ):
                            continue
                        op = comp.ops[0]
                        val = comp.comparators[0].value
                        if isinstance(op, ast.Eq) and fa3_compute_cap is None:
                            fa3_compute_cap = f"{val}.x"
                        elif isinstance(op, ast.GtE) and fa4_compute_cap is None:
                            fa4_compute_cap = f"≥{val}.0"

    # Fallback: try to parse FA4 compute caps from flash_attn_interface.py
    if fa4_compute_cap is None:
        fa4_compute_cap = _parse_fa4_supported_caps()

    return {
        "fa2": {
            "supports_fp8": False,
            "supports_sink": False,
        },
        "fa3": {
            "compute_capability": fa3_compute_cap,
            "supports_fp8": fa3_supports_fp8,
            "supports_sink": fa3_supports_sinks,
        },
        "fa4": {
            "compute_capability": fa4_compute_cap,
            "supports_fp8": False,
            "supports_sink": False,
        },
    }