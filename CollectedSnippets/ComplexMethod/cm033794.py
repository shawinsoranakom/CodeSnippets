def _ensure_imports_below_docs(self, doc_info, first_callable):
        doc_line_numbers = [lineno for lineno in (doc_info[key]['lineno'] for key in doc_info) if lineno > 0]

        min_doc_line = min(doc_line_numbers) if doc_line_numbers else None
        max_doc_line = max(doc_info[key]['end_lineno'] for key in doc_info)

        import_lines = []

        for child in self.ast.body:
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                # allow __future__ imports (the specific allowed imports are checked by other sanity tests)
                if isinstance(child, ast.ImportFrom) and child.module == '__future__':
                    continue

                import_lines.append(child.lineno)
                if min_doc_line and child.lineno < min_doc_line:
                    self.reporter.error(
                        path=self.object_path,
                        code='import-before-documentation',
                        msg=('Import found before documentation variables. '
                             'All imports must appear below '
                             'DOCUMENTATION/EXAMPLES/RETURN.'),
                        line=child.lineno
                    )
                    break
            elif isinstance(child, TRY_EXCEPT):
                bodies = child.body
                for handler in child.handlers:
                    bodies.extend(handler.body)
                for grandchild in bodies:
                    if isinstance(grandchild, (ast.Import, ast.ImportFrom)):
                        import_lines.append(grandchild.lineno)
                        if min_doc_line and grandchild.lineno < min_doc_line:
                            self.reporter.error(
                                path=self.object_path,
                                code='import-before-documentation',
                                msg=('Import found before documentation '
                                     'variables. All imports must appear below '
                                     'DOCUMENTATION/EXAMPLES/RETURN.'),
                                line=child.lineno
                            )
                            break

        for import_line in import_lines:
            if not (max_doc_line < import_line < first_callable):
                msg = (
                    'import-placement',
                    ('Imports should be directly below DOCUMENTATION/EXAMPLES/'
                     'RETURN.')
                )
                if self._is_new_module():
                    self.reporter.error(
                        path=self.object_path,
                        code=msg[0],
                        msg=msg[1],
                        line=import_line
                    )
                else:
                    self.reporter.warning(
                        path=self.object_path,
                        code=msg[0],
                        msg=msg[1],
                        line=import_line
                    )