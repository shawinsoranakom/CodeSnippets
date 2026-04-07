def __setstate__(self, state):
        # Instantiating from the tuple state that was pickled.
        wkb, srid = state
        ptr = self._from_pickle_wkb(wkb)
        if not ptr:
            raise GEOSException("Invalid Geometry loaded from pickled state.")
        self.ptr = ptr
        self._post_init()
        self.srid = srid