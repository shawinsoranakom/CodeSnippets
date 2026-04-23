def _merge_assignments(self, assignments: dict[str, cst.CSTNode], object_mapping: dict[str, set]):
        """Update the global nodes with the assignment from the modular file.

        Merging rule: if any assignment with the same name was redefined in the modular, we use it and its dependencies ONLY if it matches
        a pattern in `ASSIGNMENTS_REGEX_TO_KEEP_IF_NOT_NONE` and its value is not None, or if it matches a pattern in `ASSIGNMENTS_REGEX_TO_KEEP.
        Otherwise, we use the original value and dependencies. This rule was chosen to avoid having to rewrite the big docstrings.
        """
        for assignment, node in assignments.items():
            should_keep = any(re.search(pattern, assignment) for pattern in ASSIGNMENTS_REGEX_TO_KEEP)

            should_keep_if_not_none = any(
                re.search(pattern, assignment) for pattern in ASSIGNMENTS_REGEX_TO_KEEP_IF_NOT_NONE
            ) and not (hasattr(node.body[0].value, "value") and node.body[0].value.value == "None")

            if should_keep or should_keep_if_not_none or assignment not in self.assignments:
                self.assignments[assignment] = node
                if assignment in object_mapping:
                    self.object_dependency_mapping[assignment] = object_mapping[assignment]
        # Add them to global nodes
        self.global_nodes.update(self.assignments)