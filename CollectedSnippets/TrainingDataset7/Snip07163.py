def units(self):
        """
        Return a 2-tuple of the units value and the units name. Automatically
        determine whether to return the linear or angular units.
        """
        units, name = None, None
        if self.projected or self.local:
            units, name = capi.linear_units(self.ptr, byref(c_char_p()))
        elif self.geographic:
            units, name = capi.angular_units(self.ptr, byref(c_char_p()))
        if name is not None:
            name = force_str(name)
        return (units, name)