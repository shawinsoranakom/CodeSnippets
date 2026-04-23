def get_related_field(self):
        """
        Return the Field in the 'to' object to which this relationship is tied.
        """
        field = self.model._meta.get_field(self.field_name)
        if not field.concrete:
            raise exceptions.FieldDoesNotExist(
                "No related field named '%s'" % self.field_name
            )
        return field