def equals(self, other):
        "Return True if this geometry is equivalent to the other."
        return self._topology(capi.ogr_equals, other)