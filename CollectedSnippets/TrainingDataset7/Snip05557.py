def _check_prepopulated_fields_key(self, obj, field_name, label):
        """Check a key of `prepopulated_fields` dictionary, i.e. check that it
        is a name of existing field and the field is one of the allowed types.
        """

        try:
            field = obj.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return refer_to_missing_field(
                field=field_name, option=label, obj=obj, id="admin.E027"
            )
        else:
            if isinstance(
                field, (models.DateTimeField, models.ForeignKey, models.ManyToManyField)
            ):
                return [
                    checks.Error(
                        "The value of '%s' refers to '%s', which must not be a "
                        "DateTimeField, a ForeignKey, a OneToOneField, or a "
                        "ManyToManyField." % (label, field_name),
                        obj=obj.__class__,
                        id="admin.E028",
                    )
                ]
            else:
                return []