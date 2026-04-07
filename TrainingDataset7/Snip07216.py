def _get_z(self, index):
        return capi.cs_getz(self.ptr, index, byref(c_double()))