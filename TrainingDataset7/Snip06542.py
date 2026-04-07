def srs(self):
        """
        Return a GDAL SpatialReference object.
        """
        try:
            return gdal.SpatialReference(self.wkt)
        except Exception as e:
            wkt_error = e

        try:
            return gdal.SpatialReference(self.proj4text)
        except Exception as e:
            proj4_error = e

        raise Exception(
            "Could not get OSR SpatialReference.\n"
            f"Error for WKT '{self.wkt}': {wkt_error}\n"
            f"Error for PROJ.4 '{self.proj4text}': {proj4_error}"
        )