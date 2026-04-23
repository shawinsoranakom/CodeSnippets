def angular_name(self):
        "Return the name of the angular units."
        units, name = capi.angular_units(self.ptr, byref(c_char_p()))
        return name