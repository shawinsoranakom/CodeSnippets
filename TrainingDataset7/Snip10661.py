def _check_id_field(cls):
        """Check if `id` field is a primary key."""
        fields = [
            f for f in cls._meta.local_fields if f.name == "id" and f != cls._meta.pk
        ]
        # fields is empty or consists of the invalid "id" field
        if fields and not fields[0].primary_key and cls._meta.pk.name == "id":
            return [
                checks.Error(
                    "'id' can only be used as a field name if the field also "
                    "sets 'primary_key=True'.",
                    obj=cls,
                    id="models.E004",
                )
            ]
        else:
            return []