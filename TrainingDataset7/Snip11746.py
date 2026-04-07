def _parse_expressions(self, *expressions):
        if expressions[0] is None:
            expressions = expressions[1:]
        return super()._parse_expressions(*expressions)