def envelope(self):
        "Return the envelope for this geometry (a polygon)."
        return self._topology(capi.geos_envelope(self.ptr))