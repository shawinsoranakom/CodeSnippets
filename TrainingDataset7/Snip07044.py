def num_fields(self):
        "Return the number of fields in the Layer."
        return capi.get_field_count(self._ldefn)