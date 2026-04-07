def total_unique_constraints(self):
        """
        Return a list of total unique constraints. Useful for determining set
        of fields guaranteed to be unique for all rows.
        """
        return [
            constraint
            for constraint in self.constraints
            if (
                isinstance(constraint, UniqueConstraint)
                and constraint.condition is None
                and not constraint.contains_expressions
            )
        ]