def add_dependency(self, module_name: str, dependencies=True):
        """Given a module, add it to the dependency graph according to patterns
        specified by the user.
        """
        if (
            module_name in self.dependency_graph
            and self.dependency_graph.nodes[module_name].get("provided") is True
        ):
            return

        # Special case: PackageImporter provides a special module called
        # `torch_package_importer` that allows packaged modules to reference
        # their PackageImporter. We don't want to re-export this.
        if module_name == "torch_package_importer":
            self.dependency_graph.add_node(
                module_name,
                action=_ModuleProviderAction.SKIP,
                provided=True,
            )
            return

        if module_name == "_mock":
            self.dependency_graph.add_node(
                module_name,
                action=_ModuleProviderAction.REPACKAGED_MOCK_MODULE,
                provided=True,
            )
            return

        if self._can_implicitly_extern(module_name):
            self.dependency_graph.add_node(
                module_name, action=_ModuleProviderAction.EXTERN, provided=True
            )
            return

        for pattern, pattern_info in self.patterns.items():
            if pattern.matches(module_name):
                pattern_info.was_matched = True
                self.dependency_graph.add_node(
                    module_name, action=pattern_info.action, provided=True
                )

                if pattern_info.action == _ModuleProviderAction.DENY:
                    # Requiring a denied module just adds an error to the graph.
                    self.dependency_graph.add_node(
                        module_name, error=PackagingErrorReason.DENIED
                    )

                # If we are interning this module, we need to retrieve its
                # dependencies and package those as well.
                if pattern_info.action == _ModuleProviderAction.INTERN:
                    self._intern_module(module_name, dependencies)
                return

        # No patterns have matched. Explicitly add this as an error.
        self.dependency_graph.add_node(
            module_name, error=PackagingErrorReason.NO_ACTION
        )