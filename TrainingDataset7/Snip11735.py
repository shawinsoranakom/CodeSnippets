def get_substr(self):
        return Substr(
            self.source_expressions[0],
            self.source_expressions[1] * Value(-1),
            self.source_expressions[1],
        )