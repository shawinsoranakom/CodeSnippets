def spatialite_version(self):
        "Return the SpatiaLite library version as a string."
        return self._get_spatialite_func("spatialite_version()")