def proj(self):
        """Return the PROJ representation for this Spatial Reference."""
        return capi.to_proj(self.ptr, byref(c_char_p()))