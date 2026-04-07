def replace_expressions(self, replacements):
        if not replacements:
            return self
        if replacement := replacements.get(self):
            return replacement
        if not (source_expressions := self.get_source_expressions()):
            return self
        clone = self.copy()
        clone.set_source_expressions(
            [
                None if expr is None else expr.replace_expressions(replacements)
                for expr in source_expressions
            ]
        )
        return clone