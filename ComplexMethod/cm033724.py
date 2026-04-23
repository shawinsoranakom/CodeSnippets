def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        if self.no_targets:
            return []

        if self.text is not None:
            if self.text:
                targets = [target for target in targets if not is_binary_file(target.path)]
            else:
                targets = [target for target in targets if is_binary_file(target.path)]

        if self.extensions:
            targets = [target for target in targets if os.path.splitext(target.path)[1] in self.extensions
                       or (is_subdir(target.path, 'bin') and '.py' in self.extensions)]

        if self.exclude_extensions:
            targets = [target for target in targets if os.path.splitext(target.path)[1] not in self.exclude_extensions]

        if self.prefixes:
            targets = [target for target in targets if any(target.path.startswith(pre) for pre in self.prefixes)]

        if self.files:
            targets = [target for target in targets if os.path.basename(target.path) in self.files]

        if self.ignore_self and data_context().content.is_ansible:
            relative_self_path = os.path.relpath(self.path, data_context().content.root)
            targets = [target for target in targets if target.path != relative_self_path]

        return targets