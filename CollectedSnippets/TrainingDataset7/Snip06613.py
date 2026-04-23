def convert_extent(self, clob):
        if clob:
            # Generally, Oracle returns a polygon for the extent -- however,
            # it can return a single point if there's only one Point in the
            # table.
            ext_geom = GEOSGeometry(memoryview(clob.read()))
            gtype = str(ext_geom.geom_type)
            if gtype == "Polygon":
                # Construct the 4-tuple from the coordinates in the polygon.
                shell = ext_geom.shell
                ll, ur = shell[0][:2], shell[2][:2]
            elif gtype == "Point":
                ll = ext_geom.coords[:2]
                ur = ll
            else:
                raise Exception(
                    "Unexpected geometry type returned for extent: %s" % gtype
                )
            xmin, ymin = ll
            xmax, ymax = ur
            return (xmin, ymin, xmax, ymax)
        else:
            return None