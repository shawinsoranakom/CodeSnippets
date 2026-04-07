def _check_prepopulated_fields_value_item(self, obj, field_name, label):
        """For `prepopulated_fields` equal to {"slug": ("title",)},
        `field_name` is "title"."""

        try:
            obj.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return refer_to_missing_field(
                field=field_name, option=label, obj=obj, id="admin.E030"
            )
        else:
            return []