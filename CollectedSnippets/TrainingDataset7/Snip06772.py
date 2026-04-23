def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)

        # Setup for lazy-instantiated Geometry object.
        setattr(
            cls,
            self.attname,
            SpatialProxy(self.geom_class or GEOSGeometry, self, load_func=GEOSGeometry),
        )