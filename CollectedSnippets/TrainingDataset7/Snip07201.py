def _get_single_internal(self, index):
        return capi.get_geomn(self.ptr, index)