def test_iscounterclockwise(self):
        geom = GEOSGeometry("LINEARRING ZM (0 0 3 0, 1 0 0 2, 0 1 1 3, 0 0 3 4)")
        coord_seq = GEOSCoordSeq(capi.get_cs(geom.ptr), z=True)
        self.assertEqual(
            coord_seq.tuple,
            (
                (0.0, 0.0, 3.0, 0.0),
                (1.0, 0.0, 0.0, 2.0),
                (0.0, 1.0, 1.0, 3.0),
                (0.0, 0.0, 3.0, 4.0),
            ),
        )
        self.assertIs(coord_seq.is_counterclockwise, True)