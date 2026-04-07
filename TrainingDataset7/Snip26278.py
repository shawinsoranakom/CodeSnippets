def visit_ImportFrom(self, node):
            self.imports.update(f"{node.module}.{alias.name}" for alias in node.names)