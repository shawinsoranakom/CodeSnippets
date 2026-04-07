def unary_union(self):
        "Return the union of all the elements of this geometry."
        return self._topology(capi.geos_unary_union(self.ptr))