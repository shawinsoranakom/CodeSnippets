def is_main_has_gpu(tree: ast.AST) -> bool:
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

    for node in ast.walk(tree):
        # Detect if __name__ == "__main__":
        if isinstance(node, ast.If):
            if (
                isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
            ):
                if any(
                    isinstance(comp, ast.Constant) and comp.value == "__main__"
                    for comp in node.test.comparators
                ):
                    for inner_node in node.body:
                        if isinstance(inner_node, ast.If) and _contains_has_gpu(
                            inner_node.test
                        ):
                            return True
    return False