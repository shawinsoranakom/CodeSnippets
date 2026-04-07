def test_aswkt(self):
        wkt = (
            City.objects.annotate(
                wkt=functions.AsWKT(Point(1, 2, srid=4326)),
            )
            .first()
            .wkt
        )
        self.assertEqual(
            wkt, "POINT (1.0 2.0)" if connection.ops.oracle else "POINT(1 2)"
        )