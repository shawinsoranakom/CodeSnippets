def _set_list(self, length, items):
        """
        Create a new collection, and destroy the contents of the previous
        pointer.
        """
        prev_ptr = self.ptr
        srid = self.srid
        self.ptr = self._create_collection(length, items)
        if srid:
            self.srid = srid
        capi.destroy_geom(prev_ptr)