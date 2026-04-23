def visit_importfrom(self, node: nodes.ImportFrom) -> None:
        """Check for improper 'from _ import _' invocations."""
        if not self.current_package:
            return
        if node.level is not None:
            self._visit_importfrom_relative(self.current_package, node)
            return

        # Cache current component
        current_component: str | None = None
        for root in ("homeassistant", "tests"):
            if self.current_package.startswith(f"{root}.components."):
                current_component = self.current_package.split(".")[2]

        # Checks for hass-relative-import
        if not self._check_for_relative_import(
            self.current_package, node, current_component
        ):
            return

        if node.modname.startswith("homeassistant.components."):
            imported_parts = node.modname.split(".")
            imported_component = imported_parts[2]

            # Checks for hass-component-root-import
            if not self._check_for_component_root_import(
                node, current_component, imported_parts, imported_component
            ):
                return

            # Checks for hass-import-constant-alias
            if not self._check_for_constant_alias(
                node, current_component, imported_component
            ):
                return

        # Checks for hass-deprecated-import
        if obsolete_imports := _OBSOLETE_IMPORT.get(node.modname):
            for name_tuple in node.names:
                for obsolete_import in obsolete_imports:
                    if import_match := obsolete_import.constant.match(name_tuple[0]):
                        self.add_message(
                            "hass-deprecated-import",
                            node=node,
                            args=(import_match.string, obsolete_import.reason),
                        )

        # Checks for hass-helper-namespace-import
        if namespace_alias := _FORCE_NAMESPACE_IMPORT.get(node.modname):
            for name in node.names:
                if name[0] in namespace_alias.names:
                    self.add_message(
                        "hass-helper-namespace-import",
                        node=node,
                        args=(
                            name[0],
                            node.modname,
                            namespace_alias.alias,
                            namespace_alias.alias,
                            name[0],
                        ),
                    )