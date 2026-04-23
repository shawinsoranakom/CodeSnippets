def inverse_flattening(self):
        "Return the Inverse Flattening for this Spatial Reference."
        return capi.invflattening(self.ptr, byref(c_int()))