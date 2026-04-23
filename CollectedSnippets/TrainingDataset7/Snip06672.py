def convert_extent3d(self, box3d):
        """
        Return a 6-tuple extent for the `Extent3D` aggregate by converting
        the 3d bounding-box text returned by PostGIS (`box3d` argument), for
        example: "BOX3D(-90.0 30.0 1, -85.0 40.0 2)".
        """
        if box3d is None:
            return None
        ll, ur = box3d[6:-1].split(",")
        xmin, ymin, zmin = map(float, ll.split())
        xmax, ymax, zmax = map(float, ur.split())
        return (xmin, ymin, zmin, xmax, ymax, zmax)