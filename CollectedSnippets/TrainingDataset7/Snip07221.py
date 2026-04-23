def _set_m(self, index, value):
        capi.cs_setm(self.ptr, index, value)