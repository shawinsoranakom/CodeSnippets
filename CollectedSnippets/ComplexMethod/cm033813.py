def infer_name(self, node: astroid.nodes.Name) -> astroid.nodes.NodeNG | None:
        """Infer the node referenced by the given name, or `None` if it cannot be unambiguously inferred."""
        scope = node.scope()
        inferred: astroid.nodes.NodeNG | None = None
        name = node.name

        while scope:
            try:
                assignment = scope[name]
            except KeyError:
                scope = scope.parent.scope() if scope.parent else None
                continue

            if isinstance(assignment, astroid.nodes.AssignName) and isinstance(assignment.parent, astroid.nodes.Assign):
                inferred = assignment.parent.value
            elif (
                isinstance(scope, astroid.nodes.FunctionDef)
                and isinstance(assignment, astroid.nodes.AssignName)
                and isinstance(assignment.parent, astroid.nodes.Arguments)
                and assignment.parent.annotations
            ):
                idx, _node = assignment.parent.find_argname(name)

                if idx is not None:
                    try:
                        annotation = assignment.parent.annotations[idx]
                    except IndexError:
                        pass
                    else:
                        if isinstance(annotation, astroid.nodes.Name):
                            name = annotation.name
                            continue
            elif isinstance(assignment, astroid.nodes.ClassDef):
                inferred = assignment
            elif isinstance(assignment, astroid.nodes.ImportFrom):
                if module := self.get_module(assignment):
                    name = assignment.real_name(name)
                    scope = module.scope()
                    continue

            break

        return inferred