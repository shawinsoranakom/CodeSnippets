def linear_units(self):
        "Return the value of the linear units."
        units, name = capi.linear_units(self.ptr, byref(c_char_p()))
        return units