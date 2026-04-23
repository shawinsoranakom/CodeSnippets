def _set_list(self, length, items):
        ndim = self._cs.dims
        hasz = self._cs.hasz  # I don't understand why these are different
        srid = self.srid

        # create a new coordinate sequence and populate accordingly
        cs = GEOSCoordSeq(capi.create_cs(length, ndim), z=hasz)
        for i, c in enumerate(items):
            cs[i] = c

        ptr = self._init_func(cs.ptr)
        if ptr:
            capi.destroy_geom(self.ptr)
            self.ptr = ptr
            if srid is not None:
                self.srid = srid
            self._post_init()
        else:
            # can this happen?
            raise GEOSException("Geometry resulting from slice deletion was invalid.")