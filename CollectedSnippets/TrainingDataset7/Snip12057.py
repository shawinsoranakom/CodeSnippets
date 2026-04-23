def model_fields(self):
        """A dict mapping column names to model field names."""
        converter = connections[self.db].introspection.identifier_converter
        return {
            converter(field.column): field
            for field in self.model._meta.fields
            # Fields with None "column" should be ignored
            # (e.g. CompositePrimaryKey).
            if field.column
        }