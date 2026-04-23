def construct_change_message(form, formsets, add):
    """
    Construct a JSON structure describing changes from a changed object.
    Translations are deactivated so that strings are stored untranslated.
    Translation happens later on LogEntry access.
    """
    change_message = []
    if add:
        change_message.append({"added": {}})
    # Evaluating `form.changed_data` prior to disabling translations is
    # required to avoid fields affected by localization from being included
    # incorrectly, e.g. where date formats differ such as MM/DD/YYYY vs
    # DD/MM/YYYY.
    elif changed_data := form.changed_data:
        with translation_override(None):
            # Deactivate translations while fetching verbose_name for form
            # field labels and using `field_name`, if verbose_name is not
            # provided. Translations will happen later on LogEntry access.
            changed_field_labels = _get_changed_field_labels_from_form(
                form, changed_data
            )
        change_message.append({"changed": {"fields": changed_field_labels}})
    if formsets:
        with translation_override(None):
            for formset in formsets:
                for added_object in formset.new_objects:
                    change_message.append(
                        {
                            "added": {
                                "name": str(added_object._meta.verbose_name),
                                "object": str(added_object),
                            }
                        }
                    )
                for changed_object, changed_fields in formset.changed_objects:
                    change_message.append(
                        {
                            "changed": {
                                "name": str(changed_object._meta.verbose_name),
                                "object": str(changed_object),
                                "fields": _get_changed_field_labels_from_form(
                                    formset.forms[0], changed_fields
                                ),
                            }
                        }
                    )
                for deleted_object in formset.deleted_objects:
                    change_message.append(
                        {
                            "deleted": {
                                "name": str(deleted_object._meta.verbose_name),
                                "object": str(deleted_object),
                            }
                        }
                    )
    return change_message