def __init__(self, geom):
        # Keeping a reference to the original geometry object to prevent it
        # from being garbage collected which could then crash the prepared one
        # See #21662
        self._base_geom = geom
        from .geometry import GEOSGeometry

        if not isinstance(geom, GEOSGeometry):
            raise TypeError
        self.ptr = capi.geos_prepare(geom.ptr)