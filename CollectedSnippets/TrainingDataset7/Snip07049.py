def field_widths(self):
        "Return a list of the maximum field widths for the features."
        return [
            capi.get_field_width(capi.get_field_defn(self._ldefn, i))
            for i in range(self.num_fields)
        ]