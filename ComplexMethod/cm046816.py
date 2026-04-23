def test_no_bare_torch_import_in_functions(self):
        """All 'from torch' imports in function bodies must be inside try/except."""
        source = FORMAT_CONVERSION.read_text(encoding = "utf-8")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in ast.walk(node):
                    if (
                        isinstance(child, ast.ImportFrom)
                        and child.module
                        and child.module.startswith("torch")
                    ):
                        # This torch import must be inside a Try node
                        found_in_try = False
                        for try_node in ast.walk(node):
                            if isinstance(try_node, ast.Try):
                                for try_child in ast.walk(try_node):
                                    if try_child is child:
                                        found_in_try = True
                                        break
                            if found_in_try:
                                break
                        assert found_in_try, (
                            f"torch import at line {child.lineno} in {node.name}() "
                            "is not inside a try/except block"
                        )