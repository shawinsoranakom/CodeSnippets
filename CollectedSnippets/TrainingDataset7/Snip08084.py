def _check_field_name(self):
        field_name = self._get_field_name()
        try:
            field = self.model._meta.get_field(field_name)
        except FieldDoesNotExist:
            return [
                checks.Error(
                    "CurrentSiteManager could not find a field named '%s'."
                    % field_name,
                    obj=self,
                    id="sites.E001",
                )
            ]

        if not field.many_to_many and not isinstance(field, (models.ForeignKey)):
            return [
                checks.Error(
                    "CurrentSiteManager cannot use '%s.%s' as it is not a foreign key "
                    "or a many-to-many field."
                    % (self.model._meta.object_name, field_name),
                    obj=self,
                    id="sites.E002",
                )
            ]

        return []