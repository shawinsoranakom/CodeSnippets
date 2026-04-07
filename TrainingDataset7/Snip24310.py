def test_clone_m_dimension(self):
        geom = GEOSGeometry("POINT ZM (1 2 3 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        clone = coord_seq.clone()
        self.assertEqual(clone.tuple, (1, 2, 3, 4))
        self.assertIs(clone.hasz, True)
        self.assertIs(clone.hasm, True)

        geom = GEOSGeometry("POINT M (1 2 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=False)
        clone = coord_seq.clone()
        self.assertEqual(clone.tuple, (1, 2, 4))
        self.assertIs(clone.hasz, False)
        self.assertIs(clone.hasm, True)