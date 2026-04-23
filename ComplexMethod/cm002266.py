def _get_auto_docstring_names(file_path: str, cache: dict[str, set[str]] | None = None) -> set[str]:
    """
    Parse a source file once and return the set of class/function names decorated with @auto_docstring.
    Walks top-level definitions and one level into class bodies (methods).
    Results can be cached per file path.
    """
    if cache is not None and file_path in cache:
        return cache[file_path]

    names = set()
    try:
        with open(file_path) as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if any(_is_auto_docstring_decorator(dec) for dec in node.decorator_list):
                    names.add(node.name)
                # Also check methods inside classes
                if isinstance(node, ast.ClassDef):
                    for class_item in node.body:
                        if isinstance(class_item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            if any(_is_auto_docstring_decorator(dec) for dec in class_item.decorator_list):
                                names.add(class_item.name)
    except (OSError, SyntaxError):
        pass

    if cache is not None:
        cache[file_path] = names
    return names