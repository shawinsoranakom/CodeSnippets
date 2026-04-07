def _set_z(self, index, value):
        capi.cs_setz(self.ptr, index, value)