def dims(self):
        "Return the dimensions of this coordinate sequence."
        return capi.cs_getdims(self.ptr, byref(c_uint()))