def as_string(self):
        "Retrieve the Field's value as a string."
        if not self.is_set:
            return None
        string = capi.get_field_as_string(self._feat.ptr, self._index)
        return force_str(string, encoding=self._feat.encoding, strings_only=True)