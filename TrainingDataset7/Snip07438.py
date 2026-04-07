def overlaps(self, other):
        return capi.prepared_overlaps(self.ptr, other.ptr)