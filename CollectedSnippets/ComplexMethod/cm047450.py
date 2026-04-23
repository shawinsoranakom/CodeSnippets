def _check_sql_injection_risky(self, node):
        # Inspired from OCA/pylint-odoo project
        # Thanks @moylop260 (Moisés López) & @nilshamerlinck (Nils Hamerlinck)
        current_file_bname = os.path.basename(self.linter.current_file)
        if not (
            # .execute() or .executemany()
            isinstance(node, nodes.Call) and node.args and
            ((isinstance(node.func, nodes.Attribute) and node.func.attrname in ('execute', 'executemany', 'SQL') and self._get_cursor_name(node.func) in DFTL_CURSOR_EXPR) or
            (isinstance(node.func, nodes.Name) and node.func.name == 'SQL')) and
            # ignore in test files, probably not accessible
            not current_file_bname.startswith('test_')
        ):
            return False
        if len(node.args) == 0:
            return False
        first_arg = node.args[0]
        is_concatenation = self._check_concatenation(first_arg)
        if is_concatenation is not None:
            return is_concatenation
        return True