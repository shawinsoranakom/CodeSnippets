def extent(self):
        "Return the extent (an Envelope) of this layer."
        env = OGREnvelope()
        capi.get_extent(self.ptr, byref(env), 1)
        return Envelope(env)