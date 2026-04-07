def _check_list_display_item(self, obj, item, label):
        if callable(item):
            return []
        elif hasattr(obj, item):
            return []
        try:
            field = obj.model._meta.get_field(item)
        except FieldDoesNotExist:
            try:
                field = getattr(obj.model, item)
            except AttributeError:
                try:
                    field = get_fields_from_path(obj.model, item)[-1]
                except (FieldDoesNotExist, NotRelationField):
                    return [
                        checks.Error(
                            f"The value of '{label}' refers to '{item}', which is not "
                            f"a callable or attribute of '{obj.__class__.__name__}', "
                            "or an attribute, method, or field on "
                            f"'{obj.model._meta.label}'.",
                            obj=obj.__class__,
                            id="admin.E108",
                        )
                    ]
        if (
            getattr(field, "is_relation", False)
            and (field.many_to_many or field.one_to_many)
        ) or (getattr(field, "rel", None) and field.rel.field.many_to_one):
            return [
                checks.Error(
                    f"The value of '{label}' must not be a many-to-many field or a "
                    f"reverse foreign key.",
                    obj=obj.__class__,
                    id="admin.E109",
                )
            ]
        return []