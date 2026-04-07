def test_perimeter(self):
        """
        Test the `Perimeter` function.
        """
        # Reference query:
        #  SELECT ST_Perimeter(distapp_southtexaszipcode.poly)
        #  FROM distapp_southtexaszipcode;
        perim_m = [
            18404.3550889361,
            15627.2108551001,
            20632.5588368978,
            17094.5996143697,
        ]
        tol = 2 if connection.ops.oracle else 7
        qs = SouthTexasZipcode.objects.annotate(perimeter=Perimeter("poly")).order_by(
            "name"
        )
        for i, z in enumerate(qs):
            self.assertAlmostEqual(perim_m[i], z.perimeter.m, tol)

        # Running on points; should return 0.
        qs = SouthTexasCity.objects.annotate(perim=Perimeter("point"))
        for city in qs:
            self.assertEqual(0, city.perim.m)