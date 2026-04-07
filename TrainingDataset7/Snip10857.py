def copy(self):
        copy = super().copy()
        copy.source_expressions = self.source_expressions[:]
        copy.extra = self.extra.copy()
        return copy