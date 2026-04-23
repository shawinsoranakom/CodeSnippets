def test_relate_pattern(self):
        "Testing relate() and relate_pattern()."
        g = fromstr("POINT (0 0)")
        msg = "Invalid intersection matrix pattern."
        with self.assertRaisesMessage(GEOSException, msg):
            g.relate_pattern(0, "invalid pattern, yo")
        for rg in self.geometries.relate_geoms:
            a = fromstr(rg.wkt_a)
            b = fromstr(rg.wkt_b)
            with self.subTest(rg=rg):
                self.assertEqual(rg.result, a.relate_pattern(b, rg.pattern))
                self.assertEqual(rg.pattern, a.relate(b))