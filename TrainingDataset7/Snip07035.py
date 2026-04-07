def __init__(self, layer_ptr, ds):
        """
        Initialize on an OGR C pointer to the Layer and the `DataSource` object
        that owns this layer. The `DataSource` object is required so that a
        reference to it is kept with this Layer. This prevents garbage
        collection of the `DataSource` while this Layer is still active.
        """
        if not layer_ptr:
            raise GDALException("Cannot create Layer, invalid pointer given")
        self.ptr = layer_ptr
        self._ds = ds
        self._ldefn = capi.get_layer_defn(self._ptr)
        # Does the Layer support random reading?
        self._random_read = self.test_capability(b"RandomRead")