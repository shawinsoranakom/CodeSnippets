def _set_list(self, length, items):
        # Getting the current pointer, replacing with the newly constructed
        # geometry, and destroying the old geometry.
        prev_ptr = self.ptr
        srid = self.srid
        self.ptr = self._create_polygon(length, items)
        if srid:
            self.srid = srid
        capi.destroy_geom(prev_ptr)