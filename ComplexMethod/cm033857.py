def generic_visit(self, node):
        """Overridden ``generic_visit`` that makes some assumptions about our
        use case, and improves performance by calling visitors directly instead
        of calling ``visit`` to offload calling visitors.
        """
        self._depth += 1
        depth = self._depth
        generic_visit = self.generic_visit
        visit_Assign = self.visit_Assign
        visit_Import = self.visit_Import
        visit_ImportFrom = self.visit_ImportFrom
        for field, value in ast.iter_fields(node):
            if value.__class__ is list:
                for item in value:
                    item_class = item.__class__
                    if item_class is Import:
                        visit_Import(item)
                    elif item_class is ImportFrom:
                        visit_ImportFrom(item)
                    elif not depth and item_class is Assign:
                        if not self._embed_sniffing:
                            continue  # if the module hasn't imported the `embed` module_utils module, skip assignment analysis

                        visit_Assign(item)
                    elif hasattr(item, 'end_col_offset'):
                        # ASTish without the hit of isinstance
                        generic_visit(item)
        self._depth -= 1