def conditional(self):
        return isinstance(self.output_field, fields.BooleanField)