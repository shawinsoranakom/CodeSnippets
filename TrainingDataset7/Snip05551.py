def _check_filter_item(self, obj, field_name, label):
        """Check one item of `filter_vertical` or `filter_horizontal`, i.e.
        check that given field exists and is a ManyToManyField."""

        try:
            field = obj.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return refer_to_missing_field(
                field=field_name, option=label, obj=obj, id="admin.E019"
            )
        else:
            if not field.many_to_many or isinstance(field, models.ManyToManyRel):
                return must_be(
                    "a many-to-many field", option=label, obj=obj, id="admin.E020"
                )
            elif not field.remote_field.through._meta.auto_created:
                return [
                    checks.Error(
                        f"The value of '{label}' cannot include the ManyToManyField "
                        f"'{field_name}', because that field manually specifies a "
                        f"relationship model.",
                        obj=obj.__class__,
                        id="admin.E013",
                    )
                ]
            else:
                return []