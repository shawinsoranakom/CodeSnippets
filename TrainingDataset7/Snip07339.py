def merged(self):
        """
        Return the line merge of this Geometry.
        """
        return self._topology(capi.geos_linemerge(self.ptr))