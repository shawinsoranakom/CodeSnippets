def _is_empty_container(self, node: ast.AST, ann_type: str) -> bool:
        if ann_type == "List":
            # Assigning `[]` to a `List` type gives you a Node where
            # value=List(elts=[], ctx=Load())
            if not isinstance(node, ast.List):
                return False
            if node.elts:
                return False
        elif ann_type == "Dict":
            # Assigning `{}` to a `Dict` type gives you a Node where
            # value=Dict(keys=[], values=[])
            if not isinstance(node, ast.Dict):
                return False
            if node.keys:
                return False
        elif ann_type == "Optional":
            # Assigning `None` to an `Optional` type gives you a
            # Node where value=Constant(value=None, kind=None)
            if not isinstance(node, ast.Constant):
                return False
            if node.value:  # type: ignore[attr-defined]
                return False

        return True