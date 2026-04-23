def _contains_has_gpu(node: ast.AST) -> bool:
        if isinstance(node, ast.Name) and node.id in ["HAS_GPU", "RUN_GPU"]:
            return True
        elif isinstance(node, ast.BoolOp):
            return any(_contains_has_gpu(value) for value in node.values)
        elif isinstance(node, ast.UnaryOp):
            return _contains_has_gpu(node.operand)
        elif isinstance(node, ast.Compare):
            return _contains_has_gpu(node.left) or any(
                _contains_has_gpu(comp) for comp in node.comparators
            )
        elif isinstance(node, (ast.IfExp, ast.Call)):
            return False
        return False