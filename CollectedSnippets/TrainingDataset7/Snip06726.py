def proj_version(self):
        """Return the version of the PROJ library used by SpatiaLite."""
        return self._get_spatialite_func("proj4_version()")