def _get_m(self, index):
        return capi.cs_getm(self.ptr, index, byref(c_double()))