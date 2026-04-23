def _check_fields(self, obj):
        """Check that `fields` only refer to existing fields, doesn't contain
        duplicates. Check if at most one of `fields` and `fieldsets` is
        defined.
        """

        if obj.fields is None:
            return []
        elif not isinstance(obj.fields, (list, tuple)):
            return must_be("a list or tuple", option="fields", obj=obj, id="admin.E004")
        elif obj.fieldsets:
            return [
                checks.Error(
                    "Both 'fieldsets' and 'fields' are specified.",
                    obj=obj.__class__,
                    id="admin.E005",
                )
            ]
        field_counts = collections.Counter(flatten(obj.fields))
        if duplicate_fields := [
            field for field, count in field_counts.items() if count > 1
        ]:
            return [
                checks.Error(
                    "The value of 'fields' contains duplicate field(s).",
                    hint="Remove duplicates of %s."
                    % ", ".join(map(repr, duplicate_fields)),
                    obj=obj.__class__,
                    id="admin.E006",
                )
            ]

        return list(
            chain.from_iterable(
                self._check_field_spec(obj, field_name, "fields")
                for field_name in obj.fields
            )
        )