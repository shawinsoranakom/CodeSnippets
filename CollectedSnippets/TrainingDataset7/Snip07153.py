def from_esri(self):
        "Morph this SpatialReference from ESRI's format to EPSG."
        capi.morph_from_esri(self.ptr)