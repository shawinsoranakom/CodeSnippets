def touches(self, other):
        return capi.prepared_touches(self.ptr, other.ptr)