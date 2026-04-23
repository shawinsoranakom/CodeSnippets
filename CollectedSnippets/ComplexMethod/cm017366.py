def validate(self, model, instance, exclude=None, using=DEFAULT_DB_ALIAS):
        queryset = model._default_manager.using(using)
        if self.fields:
            lookup_kwargs = {}
            generated_field_names = []
            for field_name in self.fields:
                if exclude and field_name in exclude:
                    return
                field = model._meta.get_field(field_name)
                if field.generated:
                    if exclude and self._expression_refs_exclude(
                        model, field.expression, exclude
                    ):
                        return
                    generated_field_names.append(field.name)
                else:
                    lookup_value = getattr(instance, field.attname)
                    if (
                        self.nulls_distinct is not False
                        and lookup_value is None
                        or (
                            lookup_value == ""
                            and connections[
                                using
                            ].features.interprets_empty_strings_as_nulls
                        )
                    ):
                        # A composite constraint containing NULL value cannot
                        # cause a violation since NULL != NULL in SQL.
                        return
                    lookup_kwargs[field.name] = lookup_value
            lookup_args = []
            if generated_field_names:
                field_expression_map = instance._get_field_expression_map(
                    meta=model._meta, exclude=exclude
                )
                for field_name in generated_field_names:
                    expression = field_expression_map[field_name]
                    if self.nulls_distinct is False:
                        lhs = F(field_name)
                        condition = Q(Exact(lhs, expression)) | Q(
                            IsNull(lhs, True), IsNull(expression, True)
                        )
                        lookup_args.append(condition)
                    else:
                        lookup_kwargs[field_name] = expression
            queryset = queryset.filter(*lookup_args, **lookup_kwargs)
        else:
            # Ignore constraints with excluded fields.
            if exclude and any(
                self._expression_refs_exclude(model, expression, exclude)
                for expression in self.expressions
            ):
                return
            replacements = {
                F(field): value
                for field, value in instance._get_field_expression_map(
                    meta=model._meta, exclude=exclude
                ).items()
            }
            filters = []
            for expr in self.expressions:
                if hasattr(expr, "get_expression_for_validation"):
                    expr = expr.get_expression_for_validation()
                rhs = expr.replace_expressions(replacements)
                condition = Exact(expr, rhs)
                if self.nulls_distinct is False:
                    condition = Q(condition) | Q(IsNull(expr, True), IsNull(rhs, True))
                filters.append(condition)
            queryset = queryset.filter(*filters)
        model_class_pk = instance._get_pk_val(model._meta)
        if not instance._state.adding and instance._is_pk_set(model._meta):
            queryset = queryset.exclude(pk=model_class_pk)
        if not self.condition:
            if queryset.exists():
                if (
                    self.fields
                    and self.violation_error_message
                    == self.default_violation_error_message
                ):
                    # When fields are defined, use the unique_error_message()
                    # as a default for backward compatibility.
                    validation_error_message = instance.unique_error_message(
                        model, self.fields
                    )
                    raise ValidationError(
                        validation_error_message,
                        code=validation_error_message.code,
                    )
                raise ValidationError(
                    self.get_violation_error_message(),
                    code=self.violation_error_code,
                )
        else:
            # Ignore constraints with excluded fields in condition.
            if exclude and self._expression_refs_exclude(
                model, self.condition, exclude
            ):
                return
            against = instance._get_field_expression_map(
                meta=model._meta, exclude=exclude
            )
            if (self.condition & Exists(queryset.filter(self.condition))).check(
                against, using=using
            ):
                raise ValidationError(
                    self.get_violation_error_message(),
                    code=self.violation_error_code,
                )