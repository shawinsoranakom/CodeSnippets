def converter(value, expression, connection):
            if value is not None:
                geom = GEOSGeometryBase(read(memoryview(value.read())), geom_class)
                if srid:
                    geom.srid = srid
                return geom