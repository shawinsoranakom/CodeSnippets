def test_cast_aggregate(self):
        """
        Cast a geography to a geometry field for an aggregate function that
        expects a geometry input.
        """
        if not connection.features.supports_geography:
            self.skipTest("This test needs geography support")
        expected = (
            -96.8016128540039,
            29.7633724212646,
            -95.3631439208984,
            32.782058715820,
        )
        res = City.objects.filter(name__in=("Houston", "Dallas")).aggregate(
            extent=models.Extent(Cast("point", models.PointField()))
        )
        for val, exp in zip(res["extent"], expected):
            self.assertAlmostEqual(exp, val, 4)