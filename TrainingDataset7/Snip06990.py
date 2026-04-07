def touches(self, other):
        "Return True if this geometry touches the other."
        return self._topology(capi.ogr_touches, other)