def visit_ClassDef(self, node):
        tags = {
            arg.value
            for deco in node.decorator_list
            for arg in deco.args
            if self.matches_tagged(deco)
        }
        if (
            (len({'post_install_l10n', 'external_l10n'} & tags) != 1)
            or ('post_install_l10n' in tags and 'post_install' not in tags)
            # or ('post_install_l10n' not in tags and 'post_install' in tags)
            or (('external_l10n' in tags) ^ ('external' in tags))
        ):
            if any(
                stmt.name.startswith('test_')
                for stmt in node.body
                if isinstance(stmt, ast.FunctionDef)
            ):
                return [node]
        return []