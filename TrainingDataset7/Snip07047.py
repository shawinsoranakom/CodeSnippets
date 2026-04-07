def fields(self):
        """
        Return a list of string names corresponding to each of the Fields
        available in this Layer.
        """
        return [
            force_str(
                capi.get_field_name(capi.get_field_defn(self._ldefn, i)),
                self._ds.encoding,
                strings_only=True,
            )
            for i in range(self.num_fields)
        ]