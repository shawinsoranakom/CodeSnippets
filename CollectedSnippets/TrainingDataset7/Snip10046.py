def remove_constraint(self, model, constraint):
        if isinstance(constraint, UniqueConstraint) and (
            constraint.condition
            or constraint.contains_expressions
            or constraint.include
            or constraint.deferrable
        ):
            super().remove_constraint(model, constraint)
        else:
            self._remake_table(model)