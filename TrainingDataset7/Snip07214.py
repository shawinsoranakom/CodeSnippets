def _get_x(self, index):
        return capi.cs_getx(self.ptr, index, byref(c_double()))