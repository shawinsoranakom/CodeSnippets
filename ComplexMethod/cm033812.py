def infer(self, node: astroid.nodes.NodeNG) -> astroid.nodes.NodeNG | None:
        """Return the inferred node from the given node, or `None` if it cannot be unambiguously inferred."""
        names: list[str] = []
        target: astroid.nodes.NodeNG | None = node
        inferred: astroid.typing.InferenceResult | None = None

        while target:
            if inferred := astroid.util.safe_infer(target):
                break

            if isinstance(target, astroid.nodes.Call):
                inferred = self.infer(target.func)
                break

            if isinstance(target, astroid.nodes.FunctionDef):
                inferred = target
                break

            if isinstance(target, astroid.nodes.Name):
                target = self.infer_name(target)
            elif isinstance(target, astroid.nodes.AssignName) and isinstance(target.parent, astroid.nodes.Assign):
                target = target.parent.value
            elif isinstance(target, astroid.nodes.Attribute):
                names.append(target.attrname)
                target = target.expr
            else:
                break

        for name in reversed(names):
            if isinstance(inferred, astroid.bases.Instance):
                try:
                    attr = next(iter(inferred.getattr(name)), None)
                except astroid.exceptions.AttributeInferenceError:
                    break

                if isinstance(attr, astroid.nodes.AssignAttr):
                    inferred = self.get_ansible_module(attr)
                    continue

                if isinstance(attr, astroid.nodes.FunctionDef):
                    inferred = attr
                    continue

            if not isinstance(inferred, (astroid.nodes.Module, astroid.nodes.ClassDef)):
                inferred = None
                break

            try:
                inferred = inferred[name]
            except KeyError:
                inferred = None
            else:
                inferred = self.infer(inferred)

        if isinstance(inferred, astroid.nodes.FunctionDef) and isinstance(inferred.parent, astroid.nodes.ClassDef):
            inferred = astroid.bases.BoundMethod(inferred, inferred.parent)

        return inferred