def crosses(self, other):
        "Return True if this geometry crosses the other."
        return self._topology(capi.ogr_crosses, other)