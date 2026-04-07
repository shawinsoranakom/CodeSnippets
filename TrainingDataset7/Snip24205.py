def test_area_with_regular_aggregate(self):
        # Create projected country objects, for this test to work on all
        # backends.
        for c in Country.objects.all():
            CountryWebMercator.objects.create(
                name=c.name, mpoly=c.mpoly.transform(3857, clone=True)
            )
        # Test in projected coordinate system
        qs = CountryWebMercator.objects.annotate(area_sum=Sum(functions.Area("mpoly")))
        # Some backends (e.g. Oracle) cannot group by multipolygon values, so
        # defer such fields in the aggregation query.
        for c in qs.defer("mpoly"):
            result = c.area_sum
            # If the result is a measure object, get value.
            if isinstance(result, Area):
                result = result.sq_m
            self.assertAlmostEqual((result - c.mpoly.area) / c.mpoly.area, 0)