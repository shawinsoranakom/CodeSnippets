def import_epsg(self, epsg):
        "Import the Spatial Reference from the EPSG code (an integer)."
        capi.from_epsg(self.ptr, epsg)