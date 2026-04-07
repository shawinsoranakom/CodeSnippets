def area(self):
        """
        Return the area for a LinearRing, Polygon, or MultiPolygon; 0
        otherwise.
        """
        return capi.get_area(self.ptr)