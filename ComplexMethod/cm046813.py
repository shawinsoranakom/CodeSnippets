def test_no_top_level_torch_import(self):
        """No top-level 'import torch' or 'from torch' statements."""
        source = DATA_COLLATORS.read_text(encoding = "utf-8")
        tree = ast.parse(source)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(
                        "torch"
                    ), f"Top-level 'import {alias.name}' found at line {node.lineno}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith(
                        "torch"
                    ), f"Top-level 'from {node.module}' found at line {node.lineno}"