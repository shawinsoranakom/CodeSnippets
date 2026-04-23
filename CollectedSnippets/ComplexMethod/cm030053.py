def visit_ImportFrom(self, node):
        if node.col_offset != 0:
            return
        try:
            module = "." * node.level
            if node.module:
                module += node.module
            module = _readmodule(module, self.path, self.inpackage)
        except (ImportError, SyntaxError):
            return

        for name in node.names:
            if name.name in module:
                self.tree[name.asname or name.name] = module[name.name]
            elif name.name == "*":
                for import_name, import_value in module.items():
                    if import_name.startswith("_"):
                        continue
                    self.tree[import_name] = import_value