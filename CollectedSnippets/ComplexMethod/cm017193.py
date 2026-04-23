def _delete_composed_index(self, model, fields, constraint_kwargs, sql):
        meta_constraint_names = {
            constraint.name for constraint in model._meta.constraints
        }
        meta_index_names = {constraint.name for constraint in model._meta.indexes}
        columns = [model._meta.get_field(field).column for field in fields]
        constraint_names = self._constraint_names(
            model,
            columns,
            exclude=meta_constraint_names | meta_index_names,
            **constraint_kwargs,
        )
        if (
            constraint_kwargs.get("unique") is True
            and constraint_names
            and self.connection.features.allows_multiple_constraints_on_same_fields
        ):
            # Constraint matching the unique_together name.
            default_name = str(
                self._unique_constraint_name(model._meta.db_table, columns, quote=False)
            )
            if default_name in constraint_names:
                constraint_names = [default_name]
        if len(constraint_names) != 1:
            raise ValueError(
                "Found wrong number (%s) of constraints for %s(%s)"
                % (
                    len(constraint_names),
                    model._meta.db_table,
                    ", ".join(columns),
                )
            )
        self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))