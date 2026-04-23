def _visit_importfrom_relative(
        self, current_package: str, node: nodes.ImportFrom
    ) -> None:
        """Check for improper 'from ._ import _' invocations."""
        if not current_package.startswith(
            ("homeassistant.components.", "tests.components.")
        ):
            return

        split_package = current_package.split(".")
        current_component = split_package[2]

        self._check_for_constant_alias(node, current_component, current_component)

        if node.level <= 1:
            # No need to check relative import
            return

        if not node.modname and len(split_package) == node.level + 1:
            for name in node.names:
                # Allow relative import to component root
                if name[0] != current_component:
                    self.add_message("hass-absolute-import", node=node)
                    return
            return
        if len(split_package) < node.level + 2:
            self.add_message("hass-absolute-import", node=node)