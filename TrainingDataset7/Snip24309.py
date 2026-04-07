def test_kml_m_dimension(self):
        geom = GEOSGeometry("POINT ZM (1 2 3 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        self.assertEqual(coord_seq.kml, "<coordinates>1.0,2.0,3.0</coordinates>")
        geom = GEOSGeometry("POINT M (1 2 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=False)
        self.assertEqual(coord_seq.kml, "<coordinates>1.0,2.0,0</coordinates>")