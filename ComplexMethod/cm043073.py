def safe_eval(expression, local_vars):
            tree = ast.parse(expression, mode="eval")
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    raise ValueError("Import statements are not allowed")
                if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
                    raise ValueError(f"Access to '{node.attr}' is not allowed")
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id.startswith("_"):
                        raise ValueError(f"Calling '{func.id}' is not allowed")
                    if isinstance(func, ast.Attribute) and func.attr.startswith("_"):
                        raise ValueError(f"Calling '{func.attr}' is not allowed")
            safe_globals = {"__builtins__": SAFE_BUILTINS}
            return eval(compile(tree, "<expression>", "eval"), safe_globals, local_vars)