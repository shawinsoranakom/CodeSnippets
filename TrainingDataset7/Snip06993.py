def contains(self, other):
        "Return True if this geometry contains the other."
        return self._topology(capi.ogr_contains, other)