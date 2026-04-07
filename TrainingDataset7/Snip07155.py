def to_esri(self):
        "Morph this SpatialReference to ESRI's format."
        capi.morph_to_esri(self.ptr)