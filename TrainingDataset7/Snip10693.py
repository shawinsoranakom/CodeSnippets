def validate(self, model, instance, exclude=None, using=DEFAULT_DB_ALIAS):
        against = instance._get_field_expression_map(meta=model._meta, exclude=exclude)
        # Ignore constraints with excluded fields in condition.
        if exclude and self._expression_refs_exclude(model, self.condition, exclude):
            return
        if not Q(self.condition).check(against, using=using):
            raise ValidationError(
                self.get_violation_error_message(), code=self.violation_error_code
            )