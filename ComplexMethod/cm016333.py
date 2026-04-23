def find_unimplemented_calls(
    path: str, dynamo_dir: str | None = None
) -> list[dict[str, Any]]:
    results = []
    path_obj = Path(path)

    if path_obj.is_dir():
        file_paths = path_obj.glob("**/*.py")
    else:
        file_paths = [path_obj]  # type: ignore[assignment]

    for file_path in file_paths:
        with open(file_path) as f:
            source = f.read()
            try:
                tree = ast.parse(source)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if node.name in (
                            "unimplemented",
                            "unimplemented_with_warning",
                        ):
                            continue
                    if (
                        isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name)
                        and node.func.id
                        in ("unimplemented", "unimplemented_with_warning")
                    ):
                        info: dict[str, Any] = {
                            "gb_type": None,
                            "context": None,
                            "explanation": None,
                            "hints": [],
                        }

                        for kw in node.keywords:
                            if kw.arg in info:
                                info[kw.arg] = extract_info_from_keyword(source, kw)

                        if info["gb_type"] is None:
                            continue

                        if info["hints"]:
                            hints = info["hints"]
                            expanded_hints = []
                            items = re.findall(r'"([^"]*)"', hints)
                            if items:
                                expanded_hints.extend(items)

                            if "*graph_break_hints." in hints:
                                expanded_hints.extend(expand_hints([hints], dynamo_dir))

                            info["hints"] = expanded_hints

                        results.append(info)
            except SyntaxError:
                print(f"Syntax error in {file_path}")

    return results