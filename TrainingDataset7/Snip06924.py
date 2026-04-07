def name(self):
        "Return the name of this Field."
        name = capi.get_field_name(self.ptr)
        return force_str(name, encoding=self._feat.encoding, strings_only=True)