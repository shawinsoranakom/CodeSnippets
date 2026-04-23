def _set_x(self, index, value):
        capi.cs_setx(self.ptr, index, value)