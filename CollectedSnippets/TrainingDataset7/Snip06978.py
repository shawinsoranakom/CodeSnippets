def kml(self):
        "Return the KML representation of the Geometry."
        return capi.to_kml(self.ptr, None)