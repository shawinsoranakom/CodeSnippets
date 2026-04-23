def contains(self, other):
        "Return true if other.within(this) returns true."
        return capi.geos_contains(self.ptr, other.ptr)