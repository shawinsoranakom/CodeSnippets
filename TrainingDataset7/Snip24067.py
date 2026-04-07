def test_linestring_m_dimension(self):
        geom = OGRGeometry("LINESTRING(0 1 2 10, 1 2 3 11, 2 3 4 12)")
        self.assertIs(geom.is_measured, True)
        self.assertEqual(geom.m, [10.0, 11.0, 12.0])
        self.assertEqual(geom[0], (0.0, 1.0, 2.0, 10.0))

        geom = OGRGeometry("LINESTRING M (0 1 10, 1 2 11)")
        self.assertIs(geom.is_measured, True)
        self.assertEqual(geom.m, [10.0, 11.0])
        self.assertEqual(geom[0], (0.0, 1.0, 10.0))

        geom.set_measured(False)
        self.assertIs(geom.is_measured, False)
        self.assertIs(geom.m, None)