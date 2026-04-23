def _set_y(self, index, value):
        capi.cs_sety(self.ptr, index, value)