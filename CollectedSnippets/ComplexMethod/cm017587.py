def _check_list_editable_item(self, obj, field_name, label):
        try:
            field = obj.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return refer_to_missing_field(
                field=field_name, option=label, obj=obj, id="admin.E121"
            )
        else:
            if field_name not in obj.list_display:
                return [
                    checks.Error(
                        "The value of '%s' refers to '%s', which is not "
                        "contained in 'list_display'." % (label, field_name),
                        obj=obj.__class__,
                        id="admin.E122",
                    )
                ]
            elif obj.list_display_links and field_name in obj.list_display_links:
                return [
                    checks.Error(
                        "The value of '%s' cannot be in both 'list_editable' and "
                        "'list_display_links'." % field_name,
                        obj=obj.__class__,
                        id="admin.E123",
                    )
                ]
            # If list_display[0] is in list_editable, check that
            # list_display_links is set. See #22792 and #26229 for use cases.
            elif (
                obj.list_display[0] == field_name
                and not obj.list_display_links
                and obj.list_display_links is not None
            ):
                return [
                    checks.Error(
                        "The value of '%s' refers to the first field in 'list_display' "
                        "('%s'), which cannot be used unless 'list_display_links' is "
                        "set." % (label, obj.list_display[0]),
                        obj=obj.__class__,
                        id="admin.E124",
                    )
                ]
            elif not field.editable or field.primary_key:
                return [
                    checks.Error(
                        "The value of '%s' refers to '%s', which is not editable "
                        "through the admin." % (label, field_name),
                        obj=obj.__class__,
                        id="admin.E125",
                    )
                ]
            else:
                return []