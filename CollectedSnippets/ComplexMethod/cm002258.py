def _discover_checkers() -> tuple[dict, dict]:
    """Scan utils/*.py for CHECKER_CONFIG dicts using AST (no imports).

    Each checker module may define a top-level ``CHECKER_CONFIG`` dict with
    keys: name, label, file_globs, check_args, fix_args.

    Returns (checkers_dict, file_globs_dict) matching the shapes of
    the old CHECKERS and CHECKER_FILE_GLOBS registries.
    """
    checkers = {}
    file_globs = {}

    for py_file in sorted(UTILS_DIR.glob("*.py")):
        if py_file.name == Path(__file__).name:
            continue

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except SyntaxError:
            continue

        config = None
        for node in ast.iter_child_nodes(tree):
            if (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "CHECKER_CONFIG"
            ):
                try:
                    config = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    pass
                break

        if config is None:
            continue

        missing = _CHECKER_CONFIG_KEYS - set(config)
        if missing:
            warnings.warn(
                f"CHECKER_CONFIG in {py_file.name} is missing keys: {', '.join(sorted(missing))}. Skipping.",
                stacklevel=1,
            )
            continue

        name = config["name"]
        if name in checkers:
            warnings.warn(
                f"Duplicate checker name {name!r} in {py_file.name}, already defined by {checkers[name][1]}",
                stacklevel=1,
            )

        checkers[name] = (
            config["label"],
            py_file.name,
            config["check_args"],
            config["fix_args"],
        )
        if config["file_globs"] is not None:
            file_globs[name] = config["file_globs"]

    return checkers, file_globs