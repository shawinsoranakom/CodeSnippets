def projected(self):
        """
        Return True if this SpatialReference is a projected coordinate system
         (root node is PROJCS).
        """
        return bool(capi.isprojected(self.ptr))