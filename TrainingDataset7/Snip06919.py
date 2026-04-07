def as_double(self):
        "Retrieve the Field's value as a double (float)."
        return (
            capi.get_field_as_double(self._feat.ptr, self._index)
            if self.is_set
            else None
        )