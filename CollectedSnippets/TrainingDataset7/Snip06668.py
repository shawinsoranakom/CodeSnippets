def output_field(self):
        return GeometryField(srid=self.source_expressions[0].field.srid)