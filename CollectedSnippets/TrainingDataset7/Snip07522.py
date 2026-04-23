def start_serialization(self):
        self._init_options()
        self._cts = {}  # cache of CoordTransform's
        self.stream.write('{"type": "FeatureCollection", "features": [')