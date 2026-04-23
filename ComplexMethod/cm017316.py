def check(self, model, connection):
        """Check fields, names, and conditions of indexes."""
        errors = []
        # Index name can't start with an underscore or a number (restricted
        # for cross-database compatibility with Oracle)
        if self.name[0] == "_" or self.name[0].isdigit():
            errors.append(
                checks.Error(
                    "The index name '%s' cannot start with an underscore "
                    "or a number." % self.name,
                    obj=model,
                    id="models.E033",
                ),
            )
        if len(self.name) > self.max_name_length:
            errors.append(
                checks.Error(
                    "The index name '%s' cannot be longer than %d "
                    "characters." % (self.name, self.max_name_length),
                    obj=model,
                    id="models.E034",
                ),
            )
        references = set()
        if self.contains_expressions:
            for expression in self.expressions:
                references.update(
                    ref[0] for ref in model._get_expr_references(expression)
                )
        errors.extend(
            model._check_local_fields(
                {
                    *[field for field, _ in self.fields_orders],
                    *self.include,
                    *references,
                },
                "indexes",
            )
        )
        # Database-feature checks:
        required_db_features = model._meta.required_db_features
        if not (
            connection.features.supports_partial_indexes
            or "supports_partial_indexes" in required_db_features
        ) and any(self.condition is not None for index in model._meta.indexes):
            errors.append(
                checks.Warning(
                    "%s does not support indexes with conditions."
                    % connection.display_name,
                    hint=(
                        "Conditions will be ignored. Silence this warning "
                        "if you don't care about it."
                    ),
                    obj=model,
                    id="models.W037",
                )
            )
        if not (
            connection.features.supports_covering_indexes
            or "supports_covering_indexes" in required_db_features
        ) and any(index.include for index in model._meta.indexes):
            errors.append(
                checks.Warning(
                    "%s does not support indexes with non-key columns."
                    % connection.display_name,
                    hint=(
                        "Non-key columns will be ignored. Silence this "
                        "warning if you don't care about it."
                    ),
                    obj=model,
                    id="models.W040",
                )
            )
        if not (
            connection.features.supports_expression_indexes
            or "supports_expression_indexes" in required_db_features
        ) and any(index.contains_expressions for index in model._meta.indexes):
            errors.append(
                checks.Warning(
                    "%s does not support indexes on expressions."
                    % connection.display_name,
                    hint=(
                        "An index won't be created. Silence this warning "
                        "if you don't care about it."
                    ),
                    obj=model,
                    id="models.W043",
                )
            )
        return errors