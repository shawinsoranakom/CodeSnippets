def compute_relative_order(self, missing_dependencies: set[str]) -> dict[str, int]:
        """Compute in which relative order the `missing_dependencies` should appear when the nodes are added to the final file that
        will be created based on the modular.
        """
        relative_order = {}
        idx = 0
        classes = sorted(
            [dep for dep in tuple(missing_dependencies) if dep in self.classes], key=lambda x: self.start_lines[x]
        )
        # This is because for merged dependencies, we only have relative order in the other visited file, so we need
        # to track dependency order relative to a given class
        if len(classes) > 0 and not hasattr(self, "class_dependency_mapping"):
            raise ValueError("Cannot correctly find the relative order of the dependencies.")

        remaining_dependencies = missing_dependencies.copy()

        # Start by tracking relative order class by class
        for class_name in classes:
            class_dependencies = tuple(self.class_dependency_mapping[class_name] & remaining_dependencies)
            original_dependencies = []
            merged_dependencies = []
            # We need to differentiate between nodes that were already present (we can get relative order globally) and
            # nodes that were merged (we can get relative order only relative to the class the dependencies relate to)
            for class_dep in class_dependencies:
                if class_dep in self.start_lines:
                    original_dependencies.append(class_dep)
                else:
                    merged_dependencies.append(class_dep)
            # We need to sort deterministically before actual sorting, so that entries missing (i.e. with value 1e10)
            # will always get the same order independently of the system (they come from a set, which has no deterministic order)
            original_dependencies = sorted(original_dependencies, reverse=True)
            # Sort both list according to the order in their respective file
            original_dependencies = sorted(original_dependencies, key=lambda x: self.start_lines.get(x, 1e10))
            merged_dependencies = sorted(merged_dependencies, key=lambda x: self.modular_file_start_lines[x])

            # Add all original node first, then merged ones
            for dep in original_dependencies + merged_dependencies:
                remaining_dependencies.remove(dep)
                relative_order[dep] = idx
                idx += 1
            # Add the class itself (it can sometimes already be present if the order of classes in the source file
            # does not make sense, i.e. a class is used somewhere before being defined like in `rt_detr`...)
            if class_name in remaining_dependencies:
                remaining_dependencies.remove(class_name)
                relative_order[class_name] = idx
                idx += 1

        # Now add what still remains
        remaining_dependencies = tuple(remaining_dependencies)
        original_dependencies = []
        merged_dependencies = []
        for dep in remaining_dependencies:
            if dep in self.modular_file_start_lines:
                merged_dependencies.append(dep)
            else:
                original_dependencies.append(dep)
        # We need to sort deterministically before actual sorting, so that entries missing (i.e. with value 1e10)
        # will always get the same order independently of the system (they come from a set, which has no deterministic order)
        original_dependencies = sorted(original_dependencies, reverse=True)
        # Sort both list according to the order in their respective file
        original_dependencies = sorted(original_dependencies, key=lambda x: self.start_lines.get(x, 1e10))
        merged_dependencies = sorted(merged_dependencies, key=lambda x: self.modular_file_start_lines[x])

        # Add all original node first, then merged ones
        for dep in original_dependencies + merged_dependencies:
            relative_order[dep] = idx
            idx += 1

        return relative_order