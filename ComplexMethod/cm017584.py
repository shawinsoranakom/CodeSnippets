def _check_ordering_item(self, obj, field_name, label):
        """Check that `ordering` refers to existing fields."""
        if isinstance(field_name, (Combinable, models.OrderBy)):
            if not isinstance(field_name, models.OrderBy):
                field_name = field_name.asc()
            if isinstance(field_name.expression, models.F):
                field_name = field_name.expression.name
            else:
                return []
        if field_name == "?" and len(obj.ordering) != 1:
            return [
                checks.Error(
                    "The value of 'ordering' has the random ordering marker '?', "
                    "but contains other fields as well.",
                    hint='Either remove the "?", or remove the other fields.',
                    obj=obj.__class__,
                    id="admin.E032",
                )
            ]
        elif field_name == "?":
            return []
        elif LOOKUP_SEP in field_name:
            # Skip ordering in the format field1__field2 (FIXME: checking
            # this format would be nice, but it's a little fiddly).
            return []
        else:
            field_name = field_name.removeprefix("-")
            if field_name == "pk":
                return []
            try:
                obj.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                return refer_to_missing_field(
                    field=field_name, option=label, obj=obj, id="admin.E033"
                )
            else:
                return []