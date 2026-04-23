def get_source_fields(self):
        # We're only interested in the fields of the result expressions.
        return [self.result._output_field_or_none]