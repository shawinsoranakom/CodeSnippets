def output_field(self):
        return ArrayField(self.query.output_field)