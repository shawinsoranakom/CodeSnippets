def getOrdinate(self, dimension, index):
        "Return the value for the given dimension and index."
        self._checkindex(index)
        self._checkdim(dimension)
        return capi.cs_getordinate(self.ptr, index, dimension, byref(c_double()))