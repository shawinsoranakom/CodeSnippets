def overlaps(self, other):
        "Return True if this geometry overlaps the other."
        return self._topology(capi.ogr_overlaps, other)