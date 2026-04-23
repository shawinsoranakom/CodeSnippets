def _check_relation(self, obj, parent_model):
        # There's no FK, but we do need to confirm that the ct_field and
        # ct_fk_field are valid, and that they are part of a GenericForeignKey.

        gfks = [
            f
            for f in obj.model._meta.private_fields
            if isinstance(f, GenericForeignKey)
        ]
        if not gfks:
            return [
                checks.Error(
                    "'%s' has no GenericForeignKey." % obj.model._meta.label,
                    obj=obj.__class__,
                    id="admin.E301",
                )
            ]
        else:
            # Check that the ct_field and ct_fk_fields exist
            try:
                obj.model._meta.get_field(obj.ct_field)
            except FieldDoesNotExist:
                return [
                    checks.Error(
                        "'ct_field' references '%s', which is not a field on '%s'."
                        % (
                            obj.ct_field,
                            obj.model._meta.label,
                        ),
                        obj=obj.__class__,
                        id="admin.E302",
                    )
                ]

            try:
                obj.model._meta.get_field(obj.ct_fk_field)
            except FieldDoesNotExist:
                return [
                    checks.Error(
                        "'ct_fk_field' references '%s', which is not a field on '%s'."
                        % (
                            obj.ct_fk_field,
                            obj.model._meta.label,
                        ),
                        obj=obj.__class__,
                        id="admin.E303",
                    )
                ]

            # There's one or more GenericForeignKeys; make sure that one of
            # them uses the right ct_field and ct_fk_field.
            for gfk in gfks:
                if gfk.ct_field == obj.ct_field and gfk.fk_field == obj.ct_fk_field:
                    return []

            return [
                checks.Error(
                    "'%s' has no GenericForeignKey using content type field '%s' and "
                    "object ID field '%s'."
                    % (
                        obj.model._meta.label,
                        obj.ct_field,
                        obj.ct_fk_field,
                    ),
                    obj=obj.__class__,
                    id="admin.E304",
                )
            ]