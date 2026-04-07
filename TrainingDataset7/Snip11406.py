def _check_unique_target(self):
        rel_is_string = isinstance(self.remote_field.model, str)
        if rel_is_string or not self.requires_unique_target:
            return []

        try:
            self.foreign_related_fields
        except exceptions.FieldDoesNotExist:
            return []

        if not self.foreign_related_fields:
            return []

        has_unique_constraint = any(
            rel_field.unique for rel_field in self.foreign_related_fields
        )
        if not has_unique_constraint:
            foreign_fields = {f.name for f in self.foreign_related_fields}
            remote_opts = self.remote_field.model._meta
            has_unique_constraint = (
                any(
                    frozenset(ut) <= foreign_fields
                    for ut in remote_opts.unique_together
                )
                or any(
                    frozenset(uc.fields) <= foreign_fields
                    for uc in remote_opts.total_unique_constraints
                )
                # If the model defines a composite primary key and the foreign
                # key refers to it, the target is unique.
                or (
                    frozenset(field.name for field in remote_opts.pk_fields)
                    == foreign_fields
                )
            )

        if not has_unique_constraint:
            if len(self.foreign_related_fields) > 1:
                field_combination = ", ".join(
                    f"'{rel_field.name}'" for rel_field in self.foreign_related_fields
                )
                model_name = self.remote_field.model.__name__
                return [
                    checks.Error(
                        f"No subset of the fields {field_combination} on model "
                        f"'{model_name}' is unique.",
                        hint=(
                            "Mark a single field as unique=True or add a set of "
                            "fields to a unique constraint (via unique_together "
                            "or a UniqueConstraint (without condition) in the "
                            "model Meta.constraints)."
                        ),
                        obj=self,
                        id="fields.E310",
                    )
                ]
            else:
                field_name = self.foreign_related_fields[0].name
                model_name = self.remote_field.model.__name__
                return [
                    checks.Error(
                        f"'{model_name}.{field_name}' must be unique because it is "
                        "referenced by a foreign key.",
                        hint=(
                            "Add unique=True to this field or add a "
                            "UniqueConstraint (without condition) in the model "
                            "Meta.constraints."
                        ),
                        obj=self,
                        id="fields.E311",
                    )
                ]
        return []