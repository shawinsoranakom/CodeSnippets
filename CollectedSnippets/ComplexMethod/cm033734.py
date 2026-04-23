def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        yaml_targets = [target for target in targets if os.path.splitext(target.path)[1] in ('.yml', '.yaml')]

        for plugin_type, plugin_path in sorted(data_context().content.plugin_paths.items()):
            if plugin_type == 'module_utils':
                continue

            yaml_targets.extend([target for target in targets if
                                 os.path.splitext(target.path)[1] == '.py' and
                                 os.path.basename(target.path) != '__init__.py' and
                                 is_subdir(target.path, plugin_path)])

        return yaml_targets