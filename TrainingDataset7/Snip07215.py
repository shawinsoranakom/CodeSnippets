def _get_y(self, index):
        return capi.cs_gety(self.ptr, index, byref(c_double()))