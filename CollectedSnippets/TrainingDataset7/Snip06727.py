def lwgeom_version(self):
        """Return the version of LWGEOM library used by SpatiaLite."""
        return self._get_spatialite_func("lwgeom_version()")