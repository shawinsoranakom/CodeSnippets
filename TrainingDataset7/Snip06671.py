def convert_extent(self, box):
        """
        Return a 4-tuple extent for the `Extent` aggregate by converting
        the bounding box text returned by PostGIS (`box` argument), for
        example: "BOX(-90.0 30.0, -85.0 40.0)".
        """
        if box is None:
            return None
        ll, ur = box[4:-1].split(",")
        xmin, ymin = map(float, ll.split())
        xmax, ymax = map(float, ur.split())
        return (xmin, ymin, xmax, ymax)