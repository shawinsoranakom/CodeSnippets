def layer_count(self):
        "Return the number of layers in the data source."
        return capi.get_layer_count(self._ptr)