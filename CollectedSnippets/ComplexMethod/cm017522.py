def validate(self, model, instance, exclude=None, using=DEFAULT_DB_ALIAS):
        queryset = model._default_manager.using(using)
        replacement_map = instance._get_field_expression_map(
            meta=model._meta, exclude=exclude
        )
        replacements = {F(field): value for field, value in replacement_map.items()}
        lookups = []
        for expression, operator in self.expressions:
            if isinstance(expression, str):
                expression = F(expression)
            if exclude and self._expression_refs_exclude(model, expression, exclude):
                return
            rhs_expression = expression.replace_expressions(replacements)
            if hasattr(expression, "get_expression_for_validation"):
                expression = expression.get_expression_for_validation()
            if hasattr(rhs_expression, "get_expression_for_validation"):
                rhs_expression = rhs_expression.get_expression_for_validation()
            lookup = PostgresOperatorLookup(lhs=expression, rhs=rhs_expression)
            lookup.postgres_operator = operator
            lookups.append(lookup)
        queryset = queryset.filter(*lookups)
        model_class_pk = instance._get_pk_val(model._meta)
        if not instance._state.adding and instance._is_pk_set(model._meta):
            queryset = queryset.exclude(pk=model_class_pk)
        if not self.condition:
            if queryset.exists():
                raise ValidationError(
                    self.get_violation_error_message(), code=self.violation_error_code
                )
        else:
            # Ignore constraints with excluded fields in condition.
            if exclude and self._expression_refs_exclude(
                model, self.condition, exclude
            ):
                return
            if (self.condition & Exists(queryset.filter(self.condition))).check(
                replacement_map, using=using
            ):
                raise ValidationError(
                    self.get_violation_error_message(), code=self.violation_error_code
                )