def visit_ImportFrom(self, node):
        for alias in node.names:
            if alias.asname:
                # Exclude linking aliases (`import x as y`) to avoid confusion
                # when clicking a source link to a differently named entity.
                continue
            if alias.name == "*":
                # Resolve wildcard imports.
                file = module_name_to_file_path(node.module)
                file_contents = file.read_text(encoding="utf-8")
                locator = CodeLocator.from_code(file_contents)
                self.import_locations.update(locator.import_locations)
                self.import_locations.update(
                    {n: node.module for n in locator.node_line_numbers if "." not in n}
                )
            else:
                self.import_locations[alias.name] = ("." * node.level) + (
                    node.module or ""
                )