def remove_constraint(self, model, constraint):
        if (
            isinstance(constraint, UniqueConstraint)
            and constraint.create_sql(model, self) is not None
        ):
            self._create_missing_fk_index(
                model,
                fields=constraint.fields,
                expressions=constraint.expressions,
            )
        super().remove_constraint(model, constraint)