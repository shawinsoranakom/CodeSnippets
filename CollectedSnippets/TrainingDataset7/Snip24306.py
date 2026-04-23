def test_has_m(self):
        geom = GEOSGeometry("POINT ZM (1 2 3 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        self.assertIs(coord_seq.hasm, True)

        geom = GEOSGeometry("POINT Z (1 2 3)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        self.assertIs(coord_seq.hasm, False)

        geom = GEOSGeometry("POINT M (1 2 3)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=False)
        self.assertIs(coord_seq.hasm, True)