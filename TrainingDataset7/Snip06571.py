def get_db_converters(self, expression):
        converters = super().get_db_converters(expression)
        if isinstance(expression.output_field, GeometryField):
            converters.append(self.get_geometry_converter(expression))
        return converters