def field_precisions(self):
        "Return the field precisions for the features."
        return [
            capi.get_field_precision(capi.get_field_defn(self._ldefn, i))
            for i in range(self.num_fields)
        ]