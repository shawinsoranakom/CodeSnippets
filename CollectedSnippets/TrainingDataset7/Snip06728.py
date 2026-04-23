def rttopo_version(self):
        """Return the version of RTTOPO library used by SpatiaLite."""
        return self._get_spatialite_func("rttopo_version()")