def __init__(self, geography=False, raster=False, **kwargs):
        # Only a subset of the operators and functions are available for the
        # geography type. Lookups that don't support geography will be cast to
        # geometry.
        self.geography = geography
        # Only a subset of the operators and functions are available for the
        # raster type. Lookups that don't support raster will be converted to
        # polygons. If the raster argument is set to BILATERAL, then the
        # operator cannot handle mixed geom-raster lookups.
        self.raster = raster
        super().__init__(**kwargs)