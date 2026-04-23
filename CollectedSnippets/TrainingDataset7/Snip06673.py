def geo_db_type(self, f):
        """
        Return the database field type for the given spatial field.
        """
        if f.geom_type == "RASTER":
            return "raster"

        # Type-based geometries.
        # TODO: Support 'M' extension.
        if f.dim == 3:
            geom_type = f.geom_type + "Z"
        else:
            geom_type = f.geom_type
        if f.geography:
            if f.srid != 4326:
                raise NotSupportedError(
                    "PostGIS only supports geography columns with an SRID of 4326."
                )

            return "geography(%s,%d)" % (geom_type, f.srid)
        else:
            return "geometry(%s,%d)" % (geom_type, f.srid)