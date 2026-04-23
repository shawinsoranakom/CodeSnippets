def _check_ignored_options(self, databases):
        warnings = []

        if self.has_null_arg:
            warnings.append(
                checks.Warning(
                    "null has no effect on GeneratedField.",
                    obj=self,
                    id="fields.W225",
                )
            )

        return warnings