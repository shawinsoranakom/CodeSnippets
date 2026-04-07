def is_set(self):
        "Return True if the value of this field isn't null, False otherwise."
        return capi.is_field_set(self._feat.ptr, self._index)