def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Check if derived class is placed in its own module."""
        root_name = node.root().name

        # we only want to check components
        if not root_name.startswith("homeassistant.components."):
            return
        parts = root_name.split(".")
        current_integration = parts[2]
        current_module = parts[3] if len(parts) > 3 else ""

        ancestors = list(node.ancestors())

        if current_module != "entity" and current_integration not in _ENTITY_COMPONENTS:
            top_level_ancestors = list(node.ancestors(recurs=False))

            for ancestor in top_level_ancestors:
                if ancestor.name in _BASE_ENTITY_MODULES and not any(
                    parent.name in _MODULE_CLASSES for parent in ancestors
                ):
                    self.add_message(
                        "hass-enforce-class-module",
                        node=node,
                        args=(ancestor.name, "entity"),
                    )
                    return

        for expected_module, classes in _MODULES.items():
            if expected_module in (current_module, current_integration):
                continue

            for ancestor in ancestors:
                if ancestor.name in classes:
                    self.add_message(
                        "hass-enforce-class-module",
                        node=node,
                        args=(ancestor.name, expected_module),
                    )
                    return