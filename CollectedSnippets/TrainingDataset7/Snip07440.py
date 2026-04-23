def within(self, other):
        return capi.prepared_within(self.ptr, other.ptr)