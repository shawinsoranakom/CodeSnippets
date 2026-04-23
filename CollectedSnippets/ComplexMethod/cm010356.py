def _execute_dependency_graph(self):
        """Takes a finalized dependency graph describing how to package all
        modules and executes it, writing to the ZIP archive.
        """
        self._validate_dependency_graph()

        extern_modules = []
        for module_name, attrs in self.dependency_graph.nodes.items():
            action = attrs["action"]

            if action == _ModuleProviderAction.EXTERN:
                for hook in self._extern_hooks.values():
                    hook(self, module_name)

                extern_modules.append(module_name)

            elif action == _ModuleProviderAction.MOCK:
                for hook in self._mock_hooks.values():
                    hook(self, module_name)

                self._write_mock_file()

                is_package = hasattr(self._import_module(module_name), "__path__")
                self._write_source_string(module_name, _MOCK_IMPL, is_package)

            elif action == _ModuleProviderAction.INTERN:
                for hook in self._intern_hooks.values():
                    hook(self, module_name)

                # The node in the dependency graph contains metadata that tells us
                # how to intern the module.
                if "provided" not in attrs:
                    raise AssertionError(
                        f"Module was marked `intern` but not provided: {module_name}"
                    )

                if attrs.get("is_pickle") is True:
                    # This node came from save_pickle, we don't need to write any source for it.
                    continue

                is_package = attrs["is_package"]
                source = attrs["source"]
                self._write_source_string(module_name, source, is_package)

            elif action == _ModuleProviderAction.REPACKAGED_MOCK_MODULE:
                self._write_mock_file()
            elif action == _ModuleProviderAction.SKIP:
                continue
            else:
                raise AssertionError(
                    f"Invalid action: {module_name}, {action}. Please report a bug to PyTorch."
                )

        extern_file_contents = "\n".join(extern_modules) + "\n"
        self._write(".data/extern_modules", extern_file_contents)