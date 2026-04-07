def intersects(self, other):
        return capi.prepared_intersects(self.ptr, other.ptr)