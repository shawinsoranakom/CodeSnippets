def _check_to_fields_composite_pk(self):
        from django.db.models.fields.composite import CompositePrimaryKey

        # Skip nonexistent models.
        if isinstance(self.remote_field.model, str):
            return []

        errors = []
        for to_field in self.to_fields:
            try:
                field = (
                    self.remote_field.model._meta.pk
                    if to_field is None
                    else self.remote_field.model._meta.get_field(to_field)
                )
            except exceptions.FieldDoesNotExist:
                pass
            else:
                if isinstance(field, CompositePrimaryKey):
                    errors.append(
                        checks.Error(
                            "Field defines a relation involving model "
                            f"{self.remote_field.model._meta.object_name!r} which has "
                            "a CompositePrimaryKey and such relations are not "
                            "supported.",
                            obj=self,
                            id="fields.E347",
                        )
                    )
        return errors