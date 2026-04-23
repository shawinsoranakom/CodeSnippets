def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # Setup for lazy-instantiated Raster object. For large querysets, the
        # instantiation of all GDALRasters can potentially be expensive. This
        # delays the instantiation of the objects to the moment of evaluation
        # of the raster attribute.
        setattr(cls, self.attname, SpatialProxy(gdal.GDALRaster, self))