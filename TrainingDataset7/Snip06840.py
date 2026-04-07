def __init__(self, klass, field, load_func=None):
        """
        Initialize on the given Geometry or Raster class (not an instance)
        and the corresponding field.
        """
        self._klass = klass
        self._load_func = load_func or klass
        super().__init__(field)