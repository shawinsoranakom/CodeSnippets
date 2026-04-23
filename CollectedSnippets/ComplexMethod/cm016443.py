def get_imports(self, main_module_name: str) -> list[str]:
        """Generate import statements for all discovered types."""
        imports = []
        imports_by_module = {}

        for type_name, (module, qualname) in sorted(self.discovered_types.items()):
            # Skip types from the main module (they're already imported)
            if main_module_name and module == main_module_name:
                continue

            if module not in imports_by_module:
                imports_by_module[module] = []
            if type_name not in imports_by_module[module]:  # Avoid duplicates
                imports_by_module[module].append(type_name)

        # Generate import statements
        for module, types in sorted(imports_by_module.items()):
            if len(types) == 1:
                imports.append(f"from {module} import {types[0]}")
            else:
                imports.append(f"from {module} import {', '.join(sorted(set(types)))}")

        return imports