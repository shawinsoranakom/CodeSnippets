def width(self):
        "Return the width of this Field."
        return capi.get_field_width(self.ptr)