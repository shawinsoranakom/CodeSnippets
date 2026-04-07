def _check_list_display_links_item(self, obj, field_name, label):
        if field_name not in obj.list_display:
            return [
                checks.Error(
                    "The value of '%s' refers to '%s', which is not defined in "
                    "'list_display'." % (label, field_name),
                    obj=obj.__class__,
                    id="admin.E111",
                )
            ]
        else:
            return []