def covers(self, other):
        return capi.prepared_covers(self.ptr, other.ptr)