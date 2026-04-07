def _check_date_hierarchy(self, obj):
        """Check that date_hierarchy refers to DateField or DateTimeField."""

        if obj.date_hierarchy is None:
            return []
        else:
            try:
                field = get_fields_from_path(obj.model, obj.date_hierarchy)[-1]
            except (NotRelationField, FieldDoesNotExist):
                return [
                    checks.Error(
                        "The value of 'date_hierarchy' refers to '%s', which "
                        "does not refer to a Field." % obj.date_hierarchy,
                        obj=obj.__class__,
                        id="admin.E127",
                    )
                ]
            else:
                if field.get_internal_type() not in {"DateField", "DateTimeField"}:
                    return must_be(
                        "a DateField or DateTimeField",
                        option="date_hierarchy",
                        obj=obj,
                        id="admin.E128",
                    )
                else:
                    return []