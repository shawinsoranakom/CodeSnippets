def type(self):
        "Return the OGR type of this Field."
        return capi.get_field_type(self.ptr)