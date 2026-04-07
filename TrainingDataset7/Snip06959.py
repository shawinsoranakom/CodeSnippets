def envelope(self):
        "Return the envelope for this Geometry."
        # TODO: Fix Envelope() for Point geometries.
        return Envelope(capi.get_envelope(self.ptr, byref(OGREnvelope())))