def check(self, model, connection):
        errors = model._check_local_fields({*self.fields, *self.include}, "constraints")
        required_db_features = model._meta.required_db_features
        if self.condition is not None and not (
            connection.features.supports_partial_indexes
            or "supports_partial_indexes" in required_db_features
        ):
            errors.append(
                checks.Warning(
                    f"{connection.display_name} does not support unique constraints "
                    "with conditions.",
                    hint=(
                        "A constraint won't be created. Silence this warning if you "
                        "don't care about it."
                    ),
                    obj=model,
                    id="models.W036",
                )
            )
        if self.deferrable is not None and not (
            connection.features.supports_deferrable_unique_constraints
            or "supports_deferrable_unique_constraints" in required_db_features
        ):
            errors.append(
                checks.Warning(
                    f"{connection.display_name} does not support deferrable unique "
                    "constraints.",
                    hint=(
                        "A constraint won't be created. Silence this warning if you "
                        "don't care about it."
                    ),
                    obj=model,
                    id="models.W038",
                )
            )
        if self.include and not (
            connection.features.supports_covering_indexes
            or "supports_covering_indexes" in required_db_features
        ):
            errors.append(
                checks.Warning(
                    f"{connection.display_name} does not support unique constraints "
                    "with non-key columns.",
                    hint=(
                        "A constraint won't be created. Silence this warning if you "
                        "don't care about it."
                    ),
                    obj=model,
                    id="models.W039",
                )
            )
        if self.contains_expressions and not (
            connection.features.supports_expression_indexes
            or "supports_expression_indexes" in required_db_features
        ):
            errors.append(
                checks.Warning(
                    f"{connection.display_name} does not support unique constraints on "
                    "expressions.",
                    hint=(
                        "A constraint won't be created. Silence this warning if you "
                        "don't care about it."
                    ),
                    obj=model,
                    id="models.W044",
                )
            )
        if self.nulls_distinct is not None and not (
            connection.features.supports_nulls_distinct_unique_constraints
            or "supports_nulls_distinct_unique_constraints" in required_db_features
        ):
            errors.append(
                checks.Warning(
                    f"{connection.display_name} does not support "
                    "UniqueConstraint.nulls_distinct.",
                    hint=(
                        "A constraint won't be created. Silence this warning if you "
                        "don't care about it."
                    ),
                    obj=model,
                    id="models.W047",
                )
            )
        references = set()
        if (
            connection.features.supports_partial_indexes
            or "supports_partial_indexes" not in required_db_features
        ) and isinstance(self.condition, Q):
            references.update(model._get_expr_references(self.condition))
        if self.contains_expressions and (
            connection.features.supports_expression_indexes
            or "supports_expression_indexes" not in required_db_features
        ):
            for expression in self.expressions:
                references.update(model._get_expr_references(expression))
        errors.extend(self._check_references(model, references))
        return errors