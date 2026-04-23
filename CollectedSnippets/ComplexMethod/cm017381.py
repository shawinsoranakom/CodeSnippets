def check(self, **kwargs):
        databases = kwargs.get("databases") or []
        errors = [
            *super().check(**kwargs),
            *self._check_supported(databases),
            *self._check_persistence(databases),
            *self._check_ignored_options(databases),
        ]
        output_field_clone = self.output_field.clone()
        output_field_clone.model = self.model
        output_field_checks = output_field_clone.check(databases=databases)
        if output_field_checks:
            separator = "\n    "
            error_messages = separator.join(
                f"{output_check.msg} ({output_check.id})"
                for output_check in output_field_checks
                if isinstance(output_check, checks.Error)
            )
            if error_messages:
                errors.append(
                    checks.Error(
                        "GeneratedField.output_field has errors:"
                        f"{separator}{error_messages}",
                        obj=self,
                        id="fields.E223",
                    )
                )
            warning_messages = separator.join(
                f"{output_check.msg} ({output_check.id})"
                for output_check in output_field_checks
                if isinstance(output_check, checks.Warning)
            )
            if warning_messages:
                errors.append(
                    checks.Warning(
                        "GeneratedField.output_field has warnings:"
                        f"{separator}{warning_messages}",
                        obj=self,
                        id="fields.W224",
                    )
                )
        return errors