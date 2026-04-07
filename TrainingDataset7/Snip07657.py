def check(self, **kwargs):
        errors = super().check(**kwargs)
        if self.base_field.remote_field:
            errors.append(
                checks.Error(
                    "Base field for array cannot be a related field.",
                    obj=self,
                    id="postgres.E002",
                )
            )
        else:
            base_checks = self.base_field.check(**kwargs)
            if base_checks:
                error_messages = "\n    ".join(
                    "%s (%s)" % (base_check.msg, base_check.id)
                    for base_check in base_checks
                    if isinstance(base_check, checks.Error)
                    # Prevent duplication of E005 in an E001 check.
                    and not base_check.id == "postgres.E005"
                )
                if error_messages:
                    errors.append(
                        checks.Error(
                            "Base field for array has errors:\n    %s" % error_messages,
                            obj=self,
                            id="postgres.E001",
                        )
                    )
                warning_messages = "\n    ".join(
                    "%s (%s)" % (base_check.msg, base_check.id)
                    for base_check in base_checks
                    if isinstance(base_check, checks.Warning)
                )
                if warning_messages:
                    errors.append(
                        checks.Warning(
                            "Base field for array has warnings:\n    %s"
                            % warning_messages,
                            obj=self,
                            id="postgres.W004",
                        )
                    )
        return errors