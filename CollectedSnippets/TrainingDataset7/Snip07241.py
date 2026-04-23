def size(self):
        "Return the size of this coordinate sequence."
        return capi.cs_getsize(self.ptr, byref(c_uint()))