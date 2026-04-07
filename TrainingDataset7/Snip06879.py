def __getitem__(self, index):
        "Allows use of the index [] operator to get a layer at the index."
        if isinstance(index, str):
            try:
                layer = capi.get_layer_by_name(self.ptr, force_bytes(index))
            except GDALException:
                raise IndexError("Invalid OGR layer name given: %s." % index)
        elif isinstance(index, int):
            if 0 <= index < self.layer_count:
                layer = capi.get_layer(self._ptr, index)
            else:
                raise IndexError(
                    "Index out of range when accessing layers in a datasource: %s."
                    % index
                )
        else:
            raise TypeError("Invalid index type: %s" % type(index))
        return Layer(layer, self)