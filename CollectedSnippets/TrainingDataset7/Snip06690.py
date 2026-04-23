def get_geometry_converter(self, expression):
        read = wkb_r().read
        geom_class = expression.output_field.geom_class

        def converter(value, expression, connection):
            if isinstance(value, str):  # Coming from hex strings.
                value = value.encode("ascii")
            return None if value is None else GEOSGeometryBase(read(value), geom_class)

        return converter