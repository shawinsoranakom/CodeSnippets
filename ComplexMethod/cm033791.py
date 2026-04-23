def _find_rejectlist_imports(self):
        for child in self.ast.body:
            names = []
            if isinstance(child, ast.Import):
                names.extend(child.names)
            elif isinstance(child, TRY_EXCEPT):
                bodies = child.body
                for handler in child.handlers:
                    bodies.extend(handler.body)
                for grandchild in bodies:
                    if isinstance(grandchild, ast.Import):
                        names.extend(grandchild.names)
            for name in names:
                # TODO: Add line/col
                for rejectlist_import, options in REJECTLIST_IMPORTS.items():
                    if re.search(rejectlist_import, name.name):
                        new_only = options['new_only']
                        if self._is_new_module() and new_only:
                            self.reporter.error(
                                path=self.object_path,
                                **options['error']
                            )
                        elif not new_only:
                            self.reporter.error(
                                path=self.object_path,
                                **options['error']
                            )