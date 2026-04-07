def make_valid(self):
        """
        Attempt to create a valid representation of a given invalid geometry
        without losing any of the input vertices.
        """
        return GEOSGeometry(capi.geos_makevalid(self.ptr), srid=self.srid)