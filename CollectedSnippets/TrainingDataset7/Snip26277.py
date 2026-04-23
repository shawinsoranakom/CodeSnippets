def visit_Import(self, node):
            self.imports.update(alias.name for alias in node.names)