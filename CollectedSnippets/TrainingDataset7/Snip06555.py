def get_units(cls, wkt):
        """
        Return a tuple of (unit_value, unit_name) for the given WKT without
        using any of the database fields.
        """
        return gdal.SpatialReference(wkt).units