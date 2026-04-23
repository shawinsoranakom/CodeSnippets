def __init__(self, feat, layer):
        """
        Initialize Feature from a pointer and its Layer object.
        """
        if not feat:
            raise GDALException("Cannot create OGR Feature, invalid pointer given.")
        self.ptr = feat
        self._layer = layer