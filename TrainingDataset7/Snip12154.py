def has_composite_fields(self, expressions):
        # Check for composite fields before calling the relatively costly
        # composite_fields_to_tuples.
        return any(isinstance(expression, ColPairs) for expression in expressions)