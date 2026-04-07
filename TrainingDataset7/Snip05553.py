def _check_radio_fields_key(self, obj, field_name, label):
        """Check that a key of `radio_fields` dictionary is name of existing
        field and that the field is a ForeignKey or has `choices` defined."""

        try:
            field = obj.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return refer_to_missing_field(
                field=field_name, option=label, obj=obj, id="admin.E022"
            )
        else:
            if not (isinstance(field, models.ForeignKey) or field.choices):
                return [
                    checks.Error(
                        "The value of '%s' refers to '%s', which is not an "
                        "instance of ForeignKey, and does not have a 'choices' "
                        "definition." % (label, field_name),
                        obj=obj.__class__,
                        id="admin.E023",
                    )
                ]
            else:
                return []