def get_source_fields(self):
        # Don't consider filter and order by expression as they have nothing
        # to do with the output field resolution.
        return [e._output_field_or_none for e in super().get_source_expressions()]