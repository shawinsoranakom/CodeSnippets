def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        # If a string reaches here (via a validation error on another
        # field) then just reconstruct the Geometry.
        if value and isinstance(value, str):
            value = self.deserialize(value)

        if value:
            # Check that srid of value and map match
            if value.srid and value.srid != self.map_srid:
                try:
                    ogr = value.ogr
                    ogr.transform(self.map_srid)
                    value = ogr
                except gdal.GDALException as err:
                    logger.error(
                        "Error transforming geometry from srid '%s' to srid '%s' (%s)",
                        value.srid,
                        self.map_srid,
                        err,
                    )
        context["serialized"] = self.serialize(value)
        geom_type = gdal.OGRGeomType(self.attrs["geom_type"]).name
        context["widget"]["attrs"]["geom_name"] = (
            "Geometry" if geom_type == "Unknown" else geom_type
        )
        return context