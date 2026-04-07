def json(self):
        """
        Return the GeoJSON representation of this Geometry.
        """
        return capi.to_json(self.ptr)