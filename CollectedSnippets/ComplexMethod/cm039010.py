def visit_If(self, node: ast.If) -> None:
            guard_is_type_checking = False
            test = node.test
            if isinstance(test, ast.Attribute) and isinstance(test.value, ast.Name):
                guard_is_type_checking = (
                    test.value.id == "typing" and test.attr == "TYPE_CHECKING"
                )
            elif isinstance(test, ast.Name):
                guard_is_type_checking = test.id == "TYPE_CHECKING"

            if guard_is_type_checking:
                prev = self._in_type_checking
                self._in_type_checking = True
                for child in node.body:
                    self.visit(child)
                self._in_type_checking = prev
                for child in node.orelse:
                    self.visit(child)
            else:
                self.generic_visit(node)