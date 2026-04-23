def get_source_fields(self):
        """Return the underlying field types used by this aggregate."""
        return [e._output_field_or_none for e in self.get_source_expressions()]