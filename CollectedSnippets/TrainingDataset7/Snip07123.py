def __repr__(self):
        """
        Short-hand representation because WKB may be very large.
        """
        return "<Raster object at %s>" % hex(addressof(self._ptr))