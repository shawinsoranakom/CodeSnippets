def intersects(self, other):
        "Return True if this geometry intersects with the other."
        return self._topology(capi.ogr_intersects, other)