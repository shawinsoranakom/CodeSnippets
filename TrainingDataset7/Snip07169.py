def local(self):
        """
        Return True if this SpatialReference is local (root node is LOCAL_CS).
        """
        return bool(capi.islocal(self.ptr))