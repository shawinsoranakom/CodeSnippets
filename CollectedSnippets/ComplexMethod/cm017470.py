def check_raster(self, lookup, template_params):
        spheroid = lookup.rhs_params and lookup.rhs_params[-1] == "spheroid"

        # Check which input is a raster.
        lhs_is_raster = lookup.lhs.field.geom_type == "RASTER"
        rhs_is_raster = isinstance(lookup.rhs, GDALRaster)

        # Look for band indices and inject them if provided.
        if lookup.band_lhs is not None and lhs_is_raster:
            if not isinstance(lookup.band_lhs, int):
                name = lookup.band_lhs.__class__.__name__
                raise TypeError(f"Band index must be an integer, but got {name!r}.")
            if not self.func:
                raise ValueError(
                    "Band indices are not allowed for this operator, it works on bbox "
                    "only."
                )
            template_params["lhs"] = "%s, %s" % (
                template_params["lhs"],
                lookup.band_lhs,
            )

        if lookup.band_rhs is not None and rhs_is_raster:
            if not isinstance(lookup.band_rhs, int):
                name = lookup.band_rhs.__class__.__name__
                raise TypeError(f"Band index must be an integer, but got {name!r}.")
            if not self.func:
                raise ValueError(
                    "Band indices are not allowed for this operator, it works on bbox "
                    "only."
                )
            template_params["rhs"] = "%s, %s" % (
                template_params["rhs"],
                lookup.band_rhs,
            )

        # Convert rasters to polygons if necessary.
        if not self.raster or spheroid:
            # Operators without raster support.
            if lhs_is_raster:
                template_params["lhs"] = "ST_Polygon(%s)" % template_params["lhs"]
            if rhs_is_raster:
                template_params["rhs"] = "ST_Polygon(%s)" % template_params["rhs"]
        elif self.raster == BILATERAL:
            # Operators with raster support but don't support mixed (rast-geom)
            # lookups.
            if lhs_is_raster and not rhs_is_raster:
                template_params["lhs"] = "ST_Polygon(%s)" % template_params["lhs"]
            elif rhs_is_raster and not lhs_is_raster:
                template_params["rhs"] = "ST_Polygon(%s)" % template_params["rhs"]

        return template_params