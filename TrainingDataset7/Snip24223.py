def test_transform(self):
        # Pre-transformed points for Houston and Pueblo.
        ptown = fromstr("POINT(992363.390841912 481455.395105533)", srid=2774)

        # Asserting the result of the transform operation with the values in
        #  the pre-transformed points.
        h = City.objects.annotate(pt=functions.Transform("point", ptown.srid)).get(
            name="Pueblo"
        )
        self.assertEqual(2774, h.pt.srid)
        # Precision is low due to version variations in PROJ and GDAL.
        self.assertLess(ptown.x - h.pt.x, 1)
        self.assertLess(ptown.y - h.pt.y, 1)