def visit_ClassDef(self, node):
        self.maybe_newline()
        for deco in node.decorator_list:
            self.fill("@", allow_semicolon=False)
            self.traverse(deco)
        self.fill("class " + node.name, allow_semicolon=False)
        if hasattr(node, "type_params"):
            self._type_params_helper(node.type_params)
        with self.delimit_if("(", ")", condition = node.bases or node.keywords):
            comma = False
            for e in node.bases:
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)
            for e in node.keywords:
                if comma:
                    self.write(", ")
                else:
                    comma = True
                self.traverse(e)

        with self.block():
            self._write_docstring_and_traverse_body(node)