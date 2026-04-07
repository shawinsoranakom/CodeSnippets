def contains(self, other):
        return capi.prepared_contains(self.ptr, other.ptr)