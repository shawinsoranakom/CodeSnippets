def _check_field_spec_item(self, obj, field_name, label):
        if field_name in obj.readonly_fields:
            # Stuff can be put in fields that isn't actually a model field if
            # it's in readonly_fields, readonly_fields will handle the
            # validation of such things.
            return []
        else:
            try:
                field = obj.model._meta.get_field(field_name)
            except FieldDoesNotExist:
                # If we can't find a field on the model that matches, it could
                # be an extra field on the form.
                return []
            else:
                if (
                    isinstance(field, models.ManyToManyField)
                    and not field.remote_field.through._meta.auto_created
                ):
                    return [
                        checks.Error(
                            "The value of '%s' cannot include the ManyToManyField "
                            "'%s', because that field manually specifies a "
                            "relationship model." % (label, field_name),
                            obj=obj.__class__,
                            id="admin.E013",
                        )
                    ]
                else:
                    return []