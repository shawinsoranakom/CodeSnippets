def as_int(self, is_64=False):
        "Retrieve the Field's value as an integer."
        if is_64:
            return (
                capi.get_field_as_integer64(self._feat.ptr, self._index)
                if self.is_set
                else None
            )
        else:
            return (
                capi.get_field_as_integer(self._feat.ptr, self._index)
                if self.is_set
                else None
            )