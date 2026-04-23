def index(self, field_name):
        "Return the index of the given field name."
        i = capi.get_field_index(self.ptr, force_bytes(field_name))
        if i < 0:
            raise IndexError("Invalid OFT field name given: %s." % field_name)
        return i