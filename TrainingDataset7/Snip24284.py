def test_extent(self):
        """
        Testing the `Extent` aggregate.
        """
        # Reference query:
        #  SELECT ST_extent(point)
        #  FROM geoapp_city
        #  WHERE (name='Houston' or name='Dallas');`
        #  => BOX(-96.8016128540039 29.7633724212646,-95.3631439208984
        #  32.7820587158203)
        expected = (
            -96.8016128540039,
            29.7633724212646,
            -95.3631439208984,
            32.782058715820,
        )

        qs = City.objects.filter(name__in=("Houston", "Dallas"))
        extent = qs.aggregate(Extent("point"))["point__extent"]
        for val, exp in zip(extent, expected):
            self.assertAlmostEqual(exp, val, 4)
        self.assertIsNone(
            City.objects.filter(name=("Smalltown")).aggregate(Extent("point"))[
                "point__extent"
            ]
        )