def setOrdinate(self, dimension, index, value):
        "Set the value for the given dimension and index."
        self._checkindex(index)
        self._checkdim(dimension)
        capi.cs_setordinate(self.ptr, index, dimension, value)