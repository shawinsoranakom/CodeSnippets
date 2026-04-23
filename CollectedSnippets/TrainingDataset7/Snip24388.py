def test_line_merge(self):
        "Testing line merge support"
        ref_geoms = (
            fromstr("LINESTRING(1 1, 1 1, 3 3)"),
            fromstr("MULTILINESTRING((1 1, 3 3), (3 3, 4 2))"),
        )
        ref_merged = (
            fromstr("LINESTRING(1 1, 3 3)"),
            fromstr("LINESTRING (1 1, 3 3, 4 2)"),
        )
        for geom, merged in zip(ref_geoms, ref_merged):
            self.assertEqual(merged, geom.merged)