def _just_docs(self):
        """Module can contain just docs and from __future__ boilerplate
        """
        try:
            for child in self.ast.body:
                if not isinstance(child, ast.Assign):
                    # allow string constant expressions (these are docstrings)
                    if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant) and isinstance(child.value.value, str):
                        continue

                    # allow __future__ imports (the specific allowed imports are checked by other sanity tests)
                    if isinstance(child, ast.ImportFrom) and child.module == '__future__':
                        continue

                    return False
            return True
        except AttributeError:
            return False