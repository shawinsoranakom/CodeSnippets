def _post_init(self):
        "Perform post-initialization setup."
        # Setting the coordinate sequence for the geometry (will be None on
        # geometries that do not have coordinate sequences)
        self._cs = (
            GEOSCoordSeq(capi.get_cs(self.ptr), self.hasz) if self.has_cs else None
        )