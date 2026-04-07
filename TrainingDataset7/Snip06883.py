def name(self):
        "Return the name of the data source."
        name = capi.get_ds_name(self._ptr)
        return force_str(name, self.encoding, strings_only=True)