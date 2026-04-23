def disjoint(self, other):
        return capi.prepared_disjoint(self.ptr, other.ptr)