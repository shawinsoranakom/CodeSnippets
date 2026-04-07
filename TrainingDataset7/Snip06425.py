def _check_content_type_field(self):
        """
        Check if field named `field_name` in model `model` exists and is a
        valid content_type field (is a ForeignKey to ContentType).
        """
        try:
            field = self.model._meta.get_field(self.ct_field)
        except FieldDoesNotExist:
            return [
                checks.Error(
                    "The GenericForeignKey content type references the "
                    "nonexistent field '%s.%s'."
                    % (self.model._meta.object_name, self.ct_field),
                    obj=self,
                    id="contenttypes.E002",
                )
            ]
        else:
            if not isinstance(field, models.ForeignKey):
                return [
                    checks.Error(
                        "'%s.%s' is not a ForeignKey."
                        % (self.model._meta.object_name, self.ct_field),
                        hint=(
                            "GenericForeignKeys must use a ForeignKey to "
                            "'contenttypes.ContentType' as the 'content_type' field."
                        ),
                        obj=self,
                        id="contenttypes.E003",
                    )
                ]
            elif field.remote_field.model != ContentType:
                return [
                    checks.Error(
                        "'%s.%s' is not a ForeignKey to 'contenttypes.ContentType'."
                        % (self.model._meta.object_name, self.ct_field),
                        hint=(
                            "GenericForeignKeys must use a ForeignKey to "
                            "'contenttypes.ContentType' as the 'content_type' field."
                        ),
                        obj=self,
                        id="contenttypes.E004",
                    )
                ]
            elif isinstance(field.remote_field.on_delete, DatabaseOnDelete):
                return [
                    checks.Error(
                        f"'{self.model._meta.object_name}.{self.ct_field}' cannot use "
                        "the database-level on_delete variant.",
                        hint="Change the on_delete rule to the non-database variant.",
                        obj=self,
                        id="contenttypes.E006",
                    )
                ]
            else:
                return []