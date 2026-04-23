def convert_extent(self, box):
        """
        Convert the polygon data received from SpatiaLite to min/max values.
        """
        if box is None:
            return None
        shell = GEOSGeometry(box).shell
        xmin, ymin = shell[0][:2]
        xmax, ymax = shell[2][:2]
        return (xmin, ymin, xmax, ymax)