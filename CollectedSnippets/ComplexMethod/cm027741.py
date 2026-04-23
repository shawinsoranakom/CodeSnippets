def visit_functiondef(
        self, node: nodes.FunctionDef | nodes.AsyncFunctionDef
    ) -> None:
        """Check for super calls in method body."""
        if node.name not in METHODS:
            return

        assert node.parent
        parent = node.parent.frame()
        if not isinstance(parent, nodes.ClassDef):
            return

        # Check function body for super call
        for child_node in node.body:
            while isinstance(child_node, (nodes.Expr, nodes.Await, nodes.Return)):
                child_node = child_node.value
            match child_node:
                case nodes.Call(
                    func=nodes.Attribute(
                        expr=nodes.Call(func=nodes.Name(name="super")),
                        attrname=node.name,
                    ),
                ):
                    return

        # Check for non-empty base implementation
        found_base_implementation = False
        for base in parent.ancestors():
            for method in base.mymethods():
                if method.name != node.name:
                    continue
                if method.body and not (
                    len(method.body) == 1 and isinstance(method.body[0], nodes.Pass)
                ):
                    found_base_implementation = True
                break

            if found_base_implementation:
                self.add_message(
                    "hass-missing-super-call",
                    node=node,
                    args=(node.name,),
                    confidence=INFERENCE,
                )
                break