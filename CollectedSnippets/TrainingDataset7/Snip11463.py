def _check_ignored_options(self, **kwargs):
        warnings = []

        if self.has_null_arg:
            warnings.append(
                checks.Warning(
                    "null has no effect on ManyToManyField.",
                    obj=self,
                    id="fields.W340",
                )
            )

        if self._validators:
            warnings.append(
                checks.Warning(
                    "ManyToManyField does not support validators.",
                    obj=self,
                    id="fields.W341",
                )
            )
        if self.remote_field.symmetrical and self._related_name:
            warnings.append(
                checks.Warning(
                    "related_name has no effect on ManyToManyField "
                    'with a symmetrical relationship, e.g. to "self".',
                    obj=self,
                    id="fields.W345",
                )
            )
        if self.db_comment:
            warnings.append(
                checks.Warning(
                    "db_comment has no effect on ManyToManyField.",
                    obj=self,
                    id="fields.W346",
                )
            )

        return warnings