def get_expression_for_validation(self):
        # Ignore expressions that cannot be used during a constraint
        # validation.
        if not getattr(self, "constraint_validation_compatible", True):
            try:
                (expression,) = self.get_source_expressions()
            except ValueError as e:
                raise ValueError(
                    "Expressions with constraint_validation_compatible set to False "
                    "must have only one source expression."
                ) from e
            else:
                return expression
        return self