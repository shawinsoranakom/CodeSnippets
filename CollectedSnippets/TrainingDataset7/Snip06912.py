def fields(self):
        "Return a list of fields in the Feature."
        return [
            force_str(
                capi.get_field_name(capi.get_field_defn(self._layer._ldefn, i)),
                self.encoding,
                strings_only=True,
            )
            for i in range(self.num_fields)
        ]