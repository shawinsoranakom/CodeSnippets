def test_torch_imports_only_inside_functions(self):
        """All 'from torch' imports must be inside function/method bodies."""
        source = CHAT_TEMPLATES.read_text(encoding = "utf-8")
        tree = ast.parse(source)
        torch_imports = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                module = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import):
                    module = node.names[0].name if node.names else None
                if module and module.startswith("torch"):
                    torch_imports.append(node)

        top_level = set(id(n) for n in ast.iter_child_nodes(tree))
        for imp in torch_imports:
            assert id(imp) not in top_level, (
                f"torch import at line {imp.lineno} is at top level"
                " (should be inside a function)"
            )