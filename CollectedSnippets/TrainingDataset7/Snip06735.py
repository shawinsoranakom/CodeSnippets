def get_geometry_converter(self, expression):
        geom_class = expression.output_field.geom_class
        read = wkb_r().read

        def converter(value, expression, connection):
            return None if value is None else GEOSGeometryBase(read(value), geom_class)

        return converter