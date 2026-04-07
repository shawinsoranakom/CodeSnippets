def test_wkt_writer_trim(self):
        wkt_w = WKTWriter()
        self.assertFalse(wkt_w.trim)
        self.assertEqual(
            wkt_w.write(Point(1, 1)), b"POINT (1.0000000000000000 1.0000000000000000)"
        )

        wkt_w.trim = True
        self.assertTrue(wkt_w.trim)
        self.assertEqual(wkt_w.write(Point(1, 1)), b"POINT (1 1)")
        self.assertEqual(wkt_w.write(Point(1.1, 1)), b"POINT (1.1 1)")
        self.assertEqual(
            wkt_w.write(Point(1.0 / 3, 1)), b"POINT (0.3333333333333333 1)"
        )

        wkt_w.trim = False
        self.assertFalse(wkt_w.trim)
        self.assertEqual(
            wkt_w.write(Point(1, 1)), b"POINT (1.0000000000000000 1.0000000000000000)"
        )