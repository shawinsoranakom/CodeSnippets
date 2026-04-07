def output_field(self):
        return ArrayField(self.source_expressions[0].output_field)