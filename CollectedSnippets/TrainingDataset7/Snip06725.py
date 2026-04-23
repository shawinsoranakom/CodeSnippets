def geos_version(self):
        "Return the version of GEOS used by SpatiaLite as a string."
        return self._get_spatialite_func("geos_version()")