def parse_existing_redirects(redirects_file: Path) -> dict[str, str]:
    """
    Parse redirects.py and return the existing redirects dictionary.

    Uses AST parsing for robustness.
    """
    content = redirects_file.read_text()
    tree = ast.parse(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "redirects":
                    if isinstance(node.value, ast.Dict):
                        return {
                            k.value: v.value
                            for k, v in zip(node.value.keys, node.value.values)
                            if isinstance(k, ast.Constant)
                            and isinstance(v, ast.Constant)
                        }
    return {}