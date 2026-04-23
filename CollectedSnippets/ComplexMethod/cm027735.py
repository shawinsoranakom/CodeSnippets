def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Apply relevant type hint checks on a ClassDef node."""
        ancestor: nodes.ClassDef
        checked_class_methods: set[str] = set()
        ancestors = list(node.ancestors())  # cache result for inside loop
        for class_matcher in self._class_matchers:
            skip_matcher = False
            if exclude_base_classes := class_matcher.exclude_base_classes:
                for ancestor in ancestors:
                    if ancestor.name in exclude_base_classes:
                        skip_matcher = True
                        break
            if skip_matcher:
                continue
            for ancestor in ancestors:
                if ancestor.name == class_matcher.base_class:
                    self._visit_class_functions(
                        node, class_matcher.matches, checked_class_methods
                    )