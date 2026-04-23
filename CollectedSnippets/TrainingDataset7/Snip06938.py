def __setstate__(self, state):
        wkb, srs = state
        ptr = capi.from_wkb(wkb, None, byref(c_void_p()), len(wkb))
        if not ptr:
            raise GDALException("Invalid OGRGeometry loaded from pickled state.")
        self.ptr = ptr
        self.srs = srs