def _check_unique_together(cls):
        """Check the value of "unique_together" option."""
        if not isinstance(cls._meta.unique_together, (tuple, list)):
            return [
                checks.Error(
                    "'unique_together' must be a list or tuple.",
                    obj=cls,
                    id="models.E010",
                )
            ]

        elif any(
            not isinstance(fields, (tuple, list))
            for fields in cls._meta.unique_together
        ):
            return [
                checks.Error(
                    "All 'unique_together' elements must be lists or tuples.",
                    obj=cls,
                    id="models.E011",
                )
            ]

        else:
            errors = []
            for fields in cls._meta.unique_together:
                errors.extend(cls._check_local_fields(fields, "unique_together"))
            return errors