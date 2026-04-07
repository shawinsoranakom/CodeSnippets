def _check_autocomplete_fields_item(self, obj, field_name, label):
        """
        Check that an item in `autocomplete_fields` is a ForeignKey or a
        ManyToManyField and that the item has a related ModelAdmin with
        search_fields defined.
        """
        try:
            field = obj.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return refer_to_missing_field(
                field=field_name, option=label, obj=obj, id="admin.E037"
            )
        else:
            if not field.many_to_many and not isinstance(field, models.ForeignKey):
                return must_be(
                    "a foreign key or a many-to-many field",
                    option=label,
                    obj=obj,
                    id="admin.E038",
                )
            try:
                if isinstance(field.remote_field.model, str):
                    raise NotRegistered
                related_admin = obj.admin_site.get_model_admin(field.remote_field.model)
            except NotRegistered:
                # field.remote_field.model could be a string or a class.
                remote_model = getattr(
                    field.remote_field.model, "__name__", field.remote_field.model
                )
                return [
                    checks.Error(
                        'An admin for model "%s" has to be registered '
                        "to be referenced by %s.autocomplete_fields."
                        % (
                            remote_model,
                            type(obj).__name__,
                        ),
                        obj=obj.__class__,
                        id="admin.E039",
                    )
                ]
            else:
                if not related_admin.search_fields:
                    return [
                        checks.Error(
                            '%s must define "search_fields", because it\'s '
                            "referenced by %s.autocomplete_fields."
                            % (
                                related_admin.__class__.__name__,
                                type(obj).__name__,
                            ),
                            obj=obj.__class__,
                            id="admin.E040",
                        )
                    ]
            return []