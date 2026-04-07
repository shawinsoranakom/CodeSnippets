def converter(value, expression, connection):
            if isinstance(value, str):  # Coming from hex strings.
                value = value.encode("ascii")
            return None if value is None else GEOSGeometryBase(read(value), geom_class)