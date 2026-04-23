def test_unionagg(self):
        """
        Testing the `Union` aggregate.
        """
        tx = Country.objects.get(name="Texas").mpoly
        # Houston, Dallas -- Ordering may differ depending on backend or GEOS
        # version.
        union = GEOSGeometry("MULTIPOINT(-96.801611 32.782057,-95.363151 29.763374)")
        qs = City.objects.filter(point__within=tx)
        with self.assertRaises(ValueError):
            qs.aggregate(Union("name"))
        # Using `field_name` keyword argument in one query and specifying an
        # order in the other (which should not be used because this is
        # an aggregate method on a spatial column)
        u1 = qs.aggregate(Union("point"))["point__union"]
        u2 = qs.order_by("name").aggregate(Union("point"))["point__union"]
        self.assertTrue(union.equals(u1))
        self.assertTrue(union.equals(u2))
        qs = City.objects.filter(name="NotACity")
        self.assertIsNone(qs.aggregate(Union("point"))["point__union"])