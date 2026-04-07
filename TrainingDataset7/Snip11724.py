def get_substr(self):
        return Substr(self.source_expressions[0], Value(1), self.source_expressions[1])