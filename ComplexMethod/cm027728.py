def _check_for_relative_import(
        self,
        current_package: str,
        node: nodes.ImportFrom,
        current_component: str | None,
    ) -> bool:
        """Check for hass-relative-import."""
        if node.modname == current_package or node.modname.startswith(
            f"{current_package}."
        ):
            self.add_message("hass-relative-import", node=node)
            return False

        for root in ("homeassistant", "tests"):
            if current_package.startswith(f"{root}.components."):
                if node.modname == f"{root}.components":
                    for name in node.names:
                        if name[0] == current_component:
                            self.add_message("hass-relative-import", node=node)
                            return False
                elif node.modname.startswith(f"{root}.components.{current_component}."):
                    self.add_message("hass-relative-import", node=node)
                    return False

        return True