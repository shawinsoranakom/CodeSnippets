def test_dims(self):
        geom = GEOSGeometry("POINT ZM (1 2 3 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        self.assertEqual(coord_seq.dims, 4)

        geom = GEOSGeometry("POINT M (1 2 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=False)
        self.assertEqual(coord_seq.dims, 3)

        geom = GEOSGeometry("POINT Z (1 2 3)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        self.assertEqual(coord_seq.dims, 3)

        geom = GEOSGeometry("POINT (1 2)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=False)
        self.assertEqual(coord_seq.dims, 2)