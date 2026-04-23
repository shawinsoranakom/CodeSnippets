def crosses(self, other):
        return capi.prepared_crosses(self.ptr, other.ptr)