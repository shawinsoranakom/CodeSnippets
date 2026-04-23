def precision(self):
        "Return the precision of this Field."
        return capi.get_field_precision(self.ptr)