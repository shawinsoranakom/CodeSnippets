def test12_coordtransform(self):
        "Testing initialization of a CoordTransform."
        target = SpatialReference("WGS84")
        CoordTransform(SpatialReference(srlist[0].wkt), target)