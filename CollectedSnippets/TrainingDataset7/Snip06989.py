def disjoint(self, other):
        "Return True if this geometry and the other are spatially disjoint."
        return self._topology(capi.ogr_disjoint, other)