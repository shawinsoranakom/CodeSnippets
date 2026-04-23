def output_field(self):
        return self.output_field_class(self.source_expressions[0].output_field.srid)