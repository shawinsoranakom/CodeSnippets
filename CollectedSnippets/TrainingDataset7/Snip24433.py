def test_wkt_writer_precision(self):
        wkt_w = WKTWriter()
        self.assertIsNone(wkt_w.precision)
        self.assertEqual(
            wkt_w.write(Point(1.0 / 3, 2.0 / 3)),
            b"POINT (0.3333333333333333 0.6666666666666666)",
        )

        wkt_w.precision = 1
        self.assertEqual(wkt_w.precision, 1)
        self.assertEqual(wkt_w.write(Point(1.0 / 3, 2.0 / 3)), b"POINT (0.3 0.7)")

        wkt_w.precision = 0
        self.assertEqual(wkt_w.precision, 0)
        self.assertEqual(wkt_w.write(Point(1.0 / 3, 2.0 / 3)), b"POINT (0 1)")

        wkt_w.precision = None
        self.assertIsNone(wkt_w.precision)
        self.assertEqual(
            wkt_w.write(Point(1.0 / 3, 2.0 / 3)),
            b"POINT (0.3333333333333333 0.6666666666666666)",
        )

        with self.assertRaisesMessage(
            AttributeError, "WKT output rounding precision must be "
        ):
            wkt_w.precision = "potato"