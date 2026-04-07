def name(self):
        "Return the name of this layer in the Data Source."
        name = capi.get_fd_name(self._ldefn)
        return force_str(name, self._ds.encoding, strings_only=True)