def convert_code_to_tool_schema(obj, include: list[str] = None) -> dict:
    """Converts an object (function or class) to a tool schema by inspecting the object"""
    docstring = inspect.getdoc(obj)
    # assert docstring, "no docstring found for the objects, skip registering"

    if inspect.isclass(obj):
        schema = {"type": "class", "description": remove_spaces(docstring), "methods": {}}
        for name, method in inspect.getmembers(obj, inspect.isfunction):
            if name.startswith("_") and name != "__init__":  # skip private methodss
                continue
            if include and name not in include:
                continue
            # method_doc = inspect.getdoc(method)
            method_doc = get_class_method_docstring(obj, name)
            schema["methods"][name] = function_docstring_to_schema(method, method_doc)

    elif inspect.isfunction(obj):
        schema = function_docstring_to_schema(obj, docstring)

    return schema