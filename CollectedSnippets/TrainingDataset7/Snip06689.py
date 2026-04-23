def _normalize_distance_lookup_arg(arg):
        is_raster = (
            arg.field.geom_type == "RASTER"
            if hasattr(arg, "field")
            else isinstance(arg, GDALRaster)
        )
        return ST_Polygon(arg) if is_raster else arg