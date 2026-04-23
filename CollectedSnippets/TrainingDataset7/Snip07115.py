def __init__(self, raster, prop):
        x = raster.geotransform[self.indices[prop][0]]
        y = raster.geotransform[self.indices[prop][1]]
        super().__init__([x, y])
        self._raster = raster
        self._prop = prop