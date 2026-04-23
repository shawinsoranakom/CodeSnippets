def converter(value, expression, connection):
            return None if value is None else GEOSGeometryBase(read(value), geom_class)