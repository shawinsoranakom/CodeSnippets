def _check_single_primary_key(cls):
        errors = []
        if sum(1 for f in cls._meta.local_fields if f.primary_key) > 1:
            errors.append(
                checks.Error(
                    "The model cannot have more than one field with "
                    "'primary_key=True'.",
                    obj=cls,
                    id="models.E026",
                )
            )
        return errors