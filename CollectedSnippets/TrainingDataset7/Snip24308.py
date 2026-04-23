def test_setitem(self):
        geom = GEOSGeometry("POINT ZM (1 2 3 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        coord_seq[0] = (10, 20, 30, 40)
        self.assertEqual(coord_seq.tuple, (10, 20, 30, 40))

        geom = GEOSGeometry("POINT M (1 2 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=False)
        coord_seq[0] = (10, 20, 40)
        self.assertEqual(coord_seq.tuple, (10, 20, 40))
        self.assertEqual(coord_seq.getM(0), 40)
        self.assertIs(math.isnan(coord_seq.getZ(0)), True)