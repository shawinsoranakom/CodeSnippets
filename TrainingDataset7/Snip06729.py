def geom_lib_version(self):
        """
        Return the version of the version-dependant geom library used by
        SpatiaLite.
        """
        if self.spatial_version >= (5,):
            return self.rttopo_version()
        else:
            return self.lwgeom_version()