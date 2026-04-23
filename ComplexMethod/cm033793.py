def _find_has_import(self):
        for child in self.ast.body:
            found_try_except_import = False
            found_has = False
            if isinstance(child, TRY_EXCEPT):
                bodies = child.body
                for handler in child.handlers:
                    bodies.extend(handler.body)
                for grandchild in bodies:
                    if isinstance(grandchild, ast.Import):
                        found_try_except_import = True
                    if isinstance(grandchild, ast.Assign):
                        for target in grandchild.targets:
                            if not isinstance(target, ast.Name):
                                continue
                            if target.id.lower().startswith('has_'):
                                found_has = True
            if found_try_except_import and not found_has:
                # TODO: Add line/col
                self.reporter.warning(
                    path=self.object_path,
                    code='try-except-missing-has',
                    msg='Found Try/Except block without HAS_ assignment'
                )