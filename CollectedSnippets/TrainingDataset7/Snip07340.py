def closed(self):
        """
        Return whether or not this Geometry is closed.
        """
        return capi.geos_isclosed(self.ptr)