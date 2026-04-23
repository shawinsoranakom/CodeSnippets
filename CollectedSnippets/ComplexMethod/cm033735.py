def filter_targets(self, targets: list[TestTarget]) -> list[TestTarget]:
        """Return the given list of test targets, filtered to include only those relevant for the test."""
        plugin_paths = [plugin_path for plugin_type, plugin_path in data_context().content.plugin_paths.items() if plugin_type in DOCUMENTABLE_PLUGINS]

        return [target for target in targets
                if os.path.splitext(target.path)[1] == '.py'
                and os.path.basename(target.path) != '__init__.py'
                and any(is_subdir(target.path, path) for path in plugin_paths)
                ]