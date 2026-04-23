def linear_name(self):
        "Return the name of the linear units."
        units, name = capi.linear_units(self.ptr, byref(c_char_p()))
        return name