def parse_cuda_priority_lists() -> dict[str, list[str]]:
    """Parse priority lists from cuda.py using AST.

    The structure of _get_backend_priorities is:
        if use_mla:
            if device_capability.major == 10:
                return [MLA list for SM100]
            else:
                return [MLA list for default]
        else:
            if device_capability.major == 10:
                return [Standard list for SM100]
            else:
                return [Standard list for default]
    """
    if not CUDA_PLATFORM_FILE.exists():
        return {}

    try:
        source = CUDA_PLATFORM_FILE.read_text()
        tree = ast.parse(source)
    except Exception:
        return {}

    priorities: dict[str, list[str]] = {}

    # Find the _get_backend_priorities function
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if node.name != "_get_backend_priorities":
            continue

        # Process the function body directly
        for stmt in node.body:
            if not isinstance(stmt, ast.If):
                continue

            # Check if this is the "if use_mla:" branch
            is_mla_branch = (
                isinstance(stmt.test, ast.Name) and stmt.test.id == "use_mla"
            )

            if is_mla_branch:
                _extract_priorities(stmt.body, priorities, "mla")
                if stmt.orelse:
                    _extract_priorities(stmt.orelse, priorities, "standard")
            else:
                _extract_priorities([stmt], priorities, "standard")

    return priorities