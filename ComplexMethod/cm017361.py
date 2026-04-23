def check(self, model, connection):
        errors = []
        if not (
            connection.features.supports_table_check_constraints
            or "supports_table_check_constraints" in model._meta.required_db_features
        ):
            errors.append(
                checks.Warning(
                    f"{connection.display_name} does not support check constraints.",
                    hint=(
                        "A constraint won't be created. Silence this warning if you "
                        "don't care about it."
                    ),
                    obj=model,
                    id="models.W027",
                )
            )
        elif (
            connection.features.supports_table_check_constraints
            or "supports_table_check_constraints"
            not in model._meta.required_db_features
        ):
            references = set()
            condition = self.condition
            if isinstance(condition, Q):
                references.update(model._get_expr_references(condition))
            if any(isinstance(expr, RawSQL) for expr in condition.flatten()):
                errors.append(
                    checks.Warning(
                        f"Check constraint {self.name!r} contains RawSQL() expression "
                        "and won't be validated during the model full_clean().",
                        hint="Silence this warning if you don't care about it.",
                        obj=model,
                        id="models.W045",
                    ),
                )
            errors.extend(self._check_references(model, references))
        return errors