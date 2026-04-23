def intersects(self, other):
        "Return true if disjoint return false."
        return capi.geos_intersects(self.ptr, other.ptr)