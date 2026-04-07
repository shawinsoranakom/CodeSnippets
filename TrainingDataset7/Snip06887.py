def driver_count(cls):
        """
        Return the number of GDAL/OGR data source drivers registered.
        """
        return capi.get_driver_count()