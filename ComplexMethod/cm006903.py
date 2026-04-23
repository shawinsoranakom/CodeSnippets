def create_class(code, class_name):
    """Dynamically create a class from a string of code and a specified class name.

    Args:
        code: String containing the Python code defining the class
        class_name: Name of the class to be created

    Returns:
         A function that, when called, returns an instance of the created class

    Raises:
        ValueError: If the code contains syntax errors or the class definition is invalid
    """
    if not hasattr(ast, "TypeIgnore"):
        ast.TypeIgnore = create_type_ignore_class()

    code = code.replace("from langflow import CustomComponent", "from langflow.custom import CustomComponent")
    code = code.replace(
        "from langflow.interface.custom.custom_component import CustomComponent",
        "from langflow.custom import CustomComponent",
    )

    code = DEFAULT_IMPORT_STRING + "\n" + code
    try:
        module = ast.parse(code)
        exec_globals = prepare_global_scope(module)

        class_code = extract_class_code(module, class_name)
        compiled_class = compile_class_code(class_code)

        return build_class_constructor(compiled_class, exec_globals, class_name)

    except SyntaxError as e:
        msg = f"Syntax error in code: {e!s}"
        raise ValueError(msg) from e
    except NameError as e:
        msg = f"Name error (possibly undefined variable): {e!s}"
        raise ValueError(msg) from e
    except ValidationError as e:
        messages = [error["msg"].split(",", 1) for error in e.errors()]
        error_message = "\n".join([message[1] if len(message) > 1 else message[0] for message in messages])
        raise ValueError(error_message) from e
    except Exception as e:
        msg = f"Error creating class. {type(e).__name__}({e!s})."
        raise ValueError(msg) from e