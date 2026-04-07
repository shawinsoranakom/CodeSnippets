def test_size(self):
        geom = GEOSGeometry("POINT (1 2)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=False)
        self.assertEqual(coord_seq.size, 1)

        geom = GEOSGeometry("POINT M (1 2 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=False)
        self.assertEqual(coord_seq.size, 1)