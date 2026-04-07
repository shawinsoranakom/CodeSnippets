def get(self, field):
        """
        Return the value of the field, instead of an instance of the Field
        object. May take a string of the field name or a Field object as
        parameters.
        """
        field_name = getattr(field, "name", field)
        return self[field_name].value