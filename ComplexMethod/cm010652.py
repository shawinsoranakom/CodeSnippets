def visit_Call(self, node) -> None:
        """Determine if a Call node is 'torch.jit.annotate' in __init__.

        Visit a Call node in an ``nn.Module``'s ``__init__``
        method and determine if it's ``torch.jit.annotate``. If so,
        see if it conforms to our attribute annotation rules.
        """
        # If we have an attribute that's already been annotated at the
        # class level
        if self.visiting_class_level_ann:
            return

        # If this isn't a call to `torch.jit.annotate`
        try:
            if (
                node.func.value.value.id != "torch"
                or node.func.value.attr != "jit"
                or node.func.attr != "annotate"
            ):
                self.generic_visit(node)
            elif (
                node.func.value.value.id != "jit" or node.func.value.attr != "annotate"
            ):
                self.generic_visit(node)
        except AttributeError:
            # Looks like we didn't even have the right node structure
            # to check for `torch.jit.annotate` in the first place
            self.generic_visit(node)

        # Invariant: we have a `torch.jit.annotate` or a
        # `torch.annotate` call

        # A Call Node for `torch.jit.annotate` should have an `args`
        # list of length 2 where args[0] represents the annotation and
        # args[1] represents the actual value
        if len(node.args) != 2:
            return

        if not isinstance(node.args[0], ast.Subscript):
            return

        # See notes in `visit_AnnAssign` r.e. containers

        containers = {"List", "Dict", "Optional"}

        try:
            ann_type = node.args[0].value.id  # type: ignore[attr-defined]
        except AttributeError:
            return

        if ann_type not in containers:
            return

        # Check if the assigned variable is empty
        if not self._is_empty_container(node.args[1], ann_type):
            return

        warnings.warn(
            "The TorchScript type system doesn't support "
            "instance-level annotations on empty non-base "
            "types in `__init__`. Instead, either 1) use a "
            "type annotation in the class body, or 2) wrap "
            "the type in `torch.jit.Attribute`.",
            stacklevel=2,
        )