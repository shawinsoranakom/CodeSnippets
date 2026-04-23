def angular_units(self):
        "Return the value of the angular units."
        units, name = capi.angular_units(self.ptr, byref(c_char_p()))
        return units