def within(self, other):
        "Return True if this geometry is within the other."
        return self._topology(capi.ogr_within, other)