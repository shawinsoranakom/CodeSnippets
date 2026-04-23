def visit_import(self, node: nodes.Import) -> None:
        """Check for improper `import _` invocations."""
        if self.current_package is None:
            return
        for module, _alias in node.names:
            if module.startswith(f"{self.current_package}."):
                self.add_message("hass-relative-import", node=node)
                continue
            if (
                module.startswith("homeassistant.components.")
                and len(module.split(".")) > 3
            ):
                if (
                    self.current_package.startswith("tests.components.")
                    and self.current_package.split(".")[2] == module.split(".")[2]
                ):
                    # Ignore check if the component being tested matches
                    # the component being imported from
                    continue
                self.add_message("hass-component-root-import", node=node)