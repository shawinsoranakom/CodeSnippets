def get_prep_lookup(self):
        if hasattr(self.rhs, "resolve_expression"):
            return self.rhs
        if any(hasattr(value, "resolve_expression") for value in self.rhs):
            # Wrap direct values in Value expressions so they are handled by
            # the database at compilation time, along with other expressions.
            return ExpressionList(
                *[
                    (
                        value
                        if hasattr(value, "resolve_expression")
                        else Value(value, getattr(self.lhs, "output_field", None))
                    )
                    for value in self.rhs
                ]
            )
        prepared_values = []
        for rhs_value in self.rhs:
            if (
                self.prepare_rhs
                and hasattr(self.lhs, "output_field")
                and hasattr(self.lhs.output_field, "get_prep_value")
            ):
                rhs_value = self.lhs.output_field.get_prep_value(rhs_value)
            prepared_values.append(rhs_value)
        return prepared_values