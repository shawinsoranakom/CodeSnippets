def string_to_python(code_as_string):
    parsed_code = ast.parse(code_as_string)

    # Initialize containers for different categories
    import_statements = []
    functions = []
    functions_dict = {}

    # Traverse the AST
    for node in ast.walk(parsed_code):
        # Check for import statements
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            for alias in node.names:
                # Handling the alias in import statements
                if alias.asname:
                    import_statements.append(f"import {alias.name} as {alias.asname}")
                else:
                    import_statements.append(f"import {alias.name}")
        # Check for function definitions
        elif isinstance(node, ast.FunctionDef):
            if node.name.startswith("_"):
                # ignore private functions
                continue
            docstring = ast.get_docstring(node)
            body = node.body
            if docstring:
                body = body[1:]

            code_body = ast.unparse(body[0]).replace("\n", "\n    ")

            func_info = {
                "name": node.name,
                "docstring": docstring,
                "body": code_body,
            }
            functions.append(func_info)

    for func in functions:
        # Consolidating import statements and function definition
        function_content = "\n".join(import_statements) + "\n\n"
        function_content += f"def {func['name']}():\n    \"\"\"{func['docstring']}\"\"\"\n    {func['body']}\n"

        # Adding to dictionary
        functions_dict[func["name"]] = function_content

    return functions_dict