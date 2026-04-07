def contains_properly(self, other):
        return capi.prepared_contains_properly(self.ptr, other.ptr)