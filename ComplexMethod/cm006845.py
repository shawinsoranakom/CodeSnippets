def find_graph_variable(script_path: Path) -> dict | None:
    """Parse a Python script and find the 'graph' variable assignment or 'get_graph' function.

    Args:
        script_path (Path): Path to the Python script file

    Returns:
        dict | None: Information about the graph variable or get_graph function if found, None otherwise
    """
    try:
        with script_path.open(encoding="utf-8") as f:
            content = f.read()

        # Parse the script using AST
        tree = ast.parse(content)

        # Look for 'get_graph' function definitions (preferred) or 'graph' variable assignments
        for node in ast.walk(tree):
            # Check for get_graph function definition
            if isinstance(node, ast.FunctionDef) and node.name == "get_graph":
                line_number = node.lineno
                is_async = isinstance(node, ast.AsyncFunctionDef)

                return {
                    "line_number": line_number,
                    "type": "function_definition",
                    "function": "get_graph",
                    "is_async": is_async,
                    "arg_count": len(node.args.args),
                    "source_line": content.split("\n")[line_number - 1].strip(),
                }

            # Check for async get_graph function definition
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "get_graph":
                line_number = node.lineno

                return {
                    "line_number": line_number,
                    "type": "function_definition",
                    "function": "get_graph",
                    "is_async": True,
                    "arg_count": len(node.args.args),
                    "source_line": content.split("\n")[line_number - 1].strip(),
                }

            # Fallback: look for assignments to 'graph' variable
            if isinstance(node, ast.Assign):
                # Check if any target is named 'graph'
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "graph":
                        # Found a graph assignment
                        line_number = node.lineno

                        # Try to extract some information about the assignment
                        if isinstance(node.value, ast.Call):
                            # It's a function call like Graph(...)
                            if isinstance(node.value.func, ast.Name):
                                func_name = node.value.func.id
                            elif isinstance(node.value.func, ast.Attribute):
                                # Handle cases like Graph.from_payload(...)
                                if isinstance(node.value.func.value, ast.Name):
                                    func_name = f"{node.value.func.value.id}.{node.value.func.attr}"
                                else:
                                    func_name = node.value.func.attr
                            else:
                                func_name = "Unknown"

                            # Count arguments
                            arg_count = len(node.value.args) + len(node.value.keywords)

                            return {
                                "line_number": line_number,
                                "type": "function_call",
                                "function": func_name,
                                "arg_count": arg_count,
                                "source_line": content.split("\n")[line_number - 1].strip(),
                            }
                        # Some other type of assignment
                        return {
                            "line_number": line_number,
                            "type": "assignment",
                            "source_line": content.split("\n")[line_number - 1].strip(),
                        }

    except FileNotFoundError:
        typer.echo(f"Error: File '{script_path}' not found.")
        return None
    except SyntaxError as e:
        typer.echo(f"Error: Invalid Python syntax in '{script_path}': {e}")
        return None
    except (OSError, UnicodeDecodeError) as e:
        typer.echo(f"Error parsing '{script_path}': {e}")
        return None
    else:
        # No graph variable found
        return None