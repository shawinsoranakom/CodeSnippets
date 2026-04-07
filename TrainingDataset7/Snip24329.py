def test_eq(self):
        "Testing equivalence."
        p = fromstr("POINT(5 23)")
        self.assertEqual(p, p.wkt)
        self.assertNotEqual(p, "foo")
        ls = fromstr("LINESTRING(0 0, 1 1, 5 5)")
        self.assertEqual(ls, ls.wkt)
        self.assertNotEqual(p, "bar")
        self.assertEqual(p, "POINT(5.0 23.0)")
        # Error shouldn't be raise on equivalence testing with
        # an invalid type.
        for g in (p, ls):
            with self.subTest(g=g):
                self.assertIsNotNone(g)
                self.assertNotEqual(g, {"foo": "bar"})
                self.assertIsNot(g, False)