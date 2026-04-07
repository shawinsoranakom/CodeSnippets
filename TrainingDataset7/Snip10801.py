def get_refs(self):
        refs = set()
        for expr in self.get_source_expressions():
            if expr is None:
                continue
            refs |= expr.get_refs()
        return refs