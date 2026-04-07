def scale(self):
        """
        Pixel scale in units of the raster projection.
        """
        return TransformPoint(self, "scale")