def geographic(self):
        """
        Return True if this SpatialReference is geographic
         (root node is GEOGCS).
        """
        return bool(capi.isgeographic(self.ptr))